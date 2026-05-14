#!/usr/bin/env python3
"""
Generate a realistic SEV-SNP attestation sandbox workspace.
Creates a real ECDSA P-384 key/certificate chain (ARK->ASK->VCEK) and a
properly signed synthetic attestation report binary.
"""

import os
import random
import struct
import json
import hashlib
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.backends import default_backend
import datetime

random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "attestation_package",
    "attestation_package/certs",
    "attestation_package/logs",
    "attestation_package/tmp",
    "scripts",
    "references",
    "audit_logs",
    "config",
    "data/raw",
    "data/processed",
    "docs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "config/attestation_config.json": json.dumps({
        "endpoint": "https://kdsintf.amd.com",
        "retry_count": 3,
        "timeout_seconds": 30,
        "platform": "milan"
    }, indent=2),
    "config/policy.yaml": "debug_mode: false\nmin_tcb_version: 5\nallow_smt: true\n",
    "audit_logs/run_2024_01_15.log": "INFO: Attestation started\nINFO: Certificates fetched\nERROR: Signature mismatch on stale report\n",
    "audit_logs/run_2024_01_16.log": "INFO: Attestation started\nINFO: All checks passed\nINFO: PASSED\n",
    "data/raw/chip_manifest.csv": "chip_id,platform,region\nabc123,milan,us-east\ndef456,genoa,eu-west\n",
    "data/processed/summary.json": json.dumps({"total": 2, "passed": 1, "failed": 1}),
    "docs/attestation_overview.txt": "AMD SEV-SNP attestation overview placeholder.\nSee references/ for details.\n",
    "scripts/README.txt": "Scripts directory - contains attestation helper scripts.\nDo not modify without approval.\n",
    "attestation_package/logs/previous_run.log": "Previous attestation attempt failed - stale certificates.\n",
    "attestation_package/tmp/scratch.txt": "Temporary workspace - safe to delete.\n",
    "data/raw/old_report_hex.txt": "This is a hex dump of an old report - DO NOT USE for current verification.\n" + "00" * 100 + "\n",
}
for path, content in distractors.items():
    (WORKSPACE / path).write_text(content)

# ── generate SKILL reference docs (agent needs these) ──────────────────────
# The setup_script will copy the actual SKILL.md content; here we just
# create placeholder markers so the workspace looks realistic.
(WORKSPACE / "references" / "README.txt").write_text(
    "Reference documentation for SEV-SNP attestation.\n"
)

# ══════════════════════════════════════════════════════════════════════════════
# Generate a REAL cryptographic chain: ARK → ASK → VCEK
# and a properly signed SEV-SNP report binary
# ══════════════════════════════════════════════════════════════════════════════

def make_cert(subject_name, issuer_name, subject_key, signing_key,
              is_ca=False, serial=None):
    """Create an X.509 certificate."""
    if serial is None:
        serial = x509.random_serial_number()
    now = datetime.datetime.utcnow()
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject_name)
        .issuer_name(issuer_name)
        .public_key(subject_key.public_key())
        .serial_number(serial)
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=3650))
    )
    if is_ca:
        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        )
    cert = builder.sign(signing_key, hashes.SHA384(), default_backend())
    return cert

# Generate keys
ark_key = ec.generate_private_key(ec.SECP384R1(), default_backend())
ask_key = ec.generate_private_key(ec.SECP384R1(), default_backend())
vcek_key = ec.generate_private_key(ec.SECP384R1(), default_backend())

ark_name = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "ARK-Milan"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Advanced Micro Devices"),
])
ask_name = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "ASK-Milan"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Advanced Micro Devices"),
])
vcek_name = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "VCEK-Milan"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Advanced Micro Devices"),
])

ark_cert = make_cert(ark_name, ark_name, ark_key, ark_key, is_ca=True, serial=1)
ask_cert = make_cert(ask_name, ark_name, ask_key, ark_key, is_ca=True, serial=2)
vcek_cert = make_cert(vcek_name, ask_name, vcek_key, ask_key, is_ca=False, serial=3)

# Save PEM certificates
certs_dir = WORKSPACE / "attestation_package" / "certs"
(certs_dir / "ark.pem").write_bytes(
    ark_cert.public_bytes(serialization.Encoding.PEM)
)
(certs_dir / "ask.pem").write_bytes(
    ask_cert.public_bytes(serialization.Encoding.PEM)
)
(certs_dir / "vcek.pem").write_bytes(
    vcek_cert.public_bytes(serialization.Encoding.PEM)
)

# ── build a 1184-byte report binary ────────────────────────────────────────
# Field layout per report-fields.md / manual-verification.md
# Total size: 0x4A0 = 1184 bytes

REPORT_SIZE = 1184
SIGNED_DATA_SIZE = 672  # 0x2A0

report = bytearray(REPORT_SIZE)

# VERSION at offset 0x00 (4 bytes LE) = 2
struct.pack_into('<I', report, 0x00, 2)

# GUEST_SVN at 0x04 (4 bytes LE) = 3
struct.pack_into('<I', report, 0x04, 3)

# POLICY at 0x08 (8 bytes LE): bit3=DEBUG must be 0, set SMT (bit0)=1
# policy value = 0x0001 (SMT allowed, debug=0)
policy_value = 0x00030001  # ABI_MAJOR=0, ABI_MINOR=3, SMT=1, DEBUG=0
struct.pack_into('<Q', report, 0x08, policy_value)

# FAMILY_ID at 0x10 (16 bytes)
family_id = bytes([0xDE, 0xAD, 0xBE, 0xEF] * 4)
report[0x10:0x20] = family_id

# IMAGE_ID at 0x20 (16 bytes)
image_id = bytes([0xCA, 0xFE, 0xBA, 0xBE] * 4)
report[0x20:0x30] = image_id

# VMPL at 0x30 (4 bytes) = 0
struct.pack_into('<I', report, 0x30, 0)

# SIGNATURE_ALGO at 0x34 = 1 (ECDSA P-384)
struct.pack_into('<I', report, 0x34, 1)

# TCB_VERSION at 0x38 (8 bytes): boot_loader=3, tee=3, snp=8, microcode=115
tcb = bytearray(8)
tcb[0] = 3   # boot loader SPL
tcb[1] = 3   # TEE SPL
tcb[6] = 8   # SNP SPL
tcb[7] = 115 # microcode SPL
report[0x38:0x40] = tcb

# PLATFORM_INFO at 0x40 (8 bytes): SMT_EN=1
struct.pack_into('<Q', report, 0x40, 1)

# AUTHOR_KEY_EN at 0x48 = 0
struct.pack_into('<I', report, 0x48, 0)

# REPORT_DATA at 0x50 (64 bytes) - the nonce/challenge
# Use a deterministic nonce for testing
nonce = hashlib.sha256(b"test-nonce-2024-financial-audit-42").digest()
nonce_padded = nonce + b'\x00' * 32  # pad to 64 bytes
report[0x50:0x90] = nonce_padded

# MEASUREMENT at 0x90 (48 bytes)
measurement = hashlib.sha384(b"known-good-firmware-measurement-v1.0").digest()
report[0x90:0xC0] = measurement

# HOST_DATA at 0xC0 (32 bytes)
host_data = hashlib.sha256(b"hypervisor-id-prod-cluster-7").digest()
report[0xC0:0xE0] = host_data

# CHIP_ID at 0x1A0 (64 bytes)
chip_id_seed = hashlib.sha256(b"chip-serial-AMD-EPYC-7763-unit42").digest()
chip_id = (chip_id_seed * 3)[:64]  # 64 bytes
report[0x1A0:0x1E0] = chip_id

# COMMITTED_TCB at 0x1E0 (8 bytes) - same as TCB_VERSION
report[0x1E0:0x1E8] = tcb

# CURRENT_BUILD/MINOR/MAJOR at 0x1E8-0x1EA
report[0x1E8] = 2   # CURRENT_BUILD
report[0x1E9] = 51  # CURRENT_MINOR
report[0x1EA] = 1   # CURRENT_MAJOR

# ── sign the first 672 bytes ───────────────────────────────────────────────
signed_data = bytes(report[:SIGNED_DATA_SIZE])
sig_obj = vcek_key.sign(signed_data, ec.ECDSA(hashes.SHA384()))

# Decode DER signature to get r, s integers
r_int, s_int = decode_dss_signature(sig_obj)

def int_to_le72(n):
    """Convert integer to 72-byte little-endian (AMD format: 48-byte BE -> reversed to 72-byte LE with zero padding)."""
    be_bytes = n.to_bytes(48, 'big')
    # AMD pads R and S to 72 bytes (48 meaningful + 24 zero padding at high end in LE)
    le_bytes = be_bytes[::-1]  # reverse to little-endian
    le_padded = le_bytes + b'\x00' * 24  # pad to 72
    return le_padded

r_le72 = int_to_le72(r_int)
s_le72 = int_to_le72(s_int)

# SIGNATURE at 0x2A0 (144 bytes): R(72) || S(72)
report[0x2A0:0x2A0 + 72] = r_le72
report[0x2A0 + 72:0x2A0 + 144] = s_le72

# Save the report
report_path = WORKSPACE / "attestation_package" / "report.bin"
report_path.write_bytes(bytes(report))

# ── save ground truth for eval (NOT visible to agent as hints) ─────────────
# Store as a hidden eval reference
ground_truth = {
    "version": 2,
    "policy_hex": hex(policy_value),
    "debug_bit": 0,
    "report_data_hex": nonce_padded.hex(),
    "measurement_hex": measurement.hex(),
    "chip_id_hex": chip_id.hex(),
    "signed_data_size": SIGNED_DATA_SIZE,
    "signature_offset": 0x2A0,
    "r_int": r_int,
    "s_int": s_int,
}
# Save ground truth to a hidden location outside workspace browsing
import json
Path("/tmp/eval_ground_truth.json").write_text(json.dumps(ground_truth, indent=2))

# Also save VCEK private key for eval use
Path("/tmp/vcek_key.pem").write_bytes(
    vcek_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )
)

print("Workspace generated successfully.")
print(f"Report: {report_path} ({len(report)} bytes)")
print(f"Certs: {list(certs_dir.iterdir())}")