#!/bin/bash
set -euo pipefail

# Write SKILL.md reference files that the agent can read
cat > /workspace/references/report-fields.md << 'REFEOF'
# SEV-SNP Attestation Report Fields

## Report Structure Overview

The attestation report is a 1184-byte (0x4A0) binary structure signed by the AMD Platform Security Processor (PSP). The signature covers bytes 0x00-0x29F (672 bytes).

## Key Fields

### VERSION (offset 0x00, 4 bytes)
Report format version. Currently version 2 for SEV-SNP.

### GUEST_SVN (offset 0x04, 4 bytes)
Guest Security Version Number.

### POLICY (offset 0x08, 8 bytes)
Guest policy flags:
| Bit | Name | Description |
|-----|------|-------------|
| 0 | SMT | Allow SMT |
| 3 | DEBUG | Debug mode (should NOT be trusted if set) |

**Security Note**: If bit 3 (DEBUG) is set, the VM is in debug mode and should NOT be trusted with secrets.

### REPORT_DATA (offset 0x50, 64 bytes)
**Critical field**: Guest-provided data (nonce/challenge).

### MEASUREMENT (offset 0x90, 48 bytes)
**Critical field**: SHA-384 hash of initial guest memory.

### CHIP_ID (offset 0x1A0, 64 bytes)
**Critical field**: Unique AMD chip identifier.

### SIGNATURE (offset 0x2A0, 144 bytes)
ECDSA P-384 signature over bytes 0x00-0x29F.
Format: R (72 bytes, little-endian) || S (72 bytes, little-endian)
REFEOF

cat > /workspace/references/manual-verification.md << 'MVEOF'
# Manual SEV-SNP Verification with OpenSSL

## Step 1: Understand Report Structure

The SEV-SNP attestation report is 1184 bytes (0x4A0):

```
Offset    Size    Field
------    ----    -----
0x000     672     Signed data
0x2A0     144     Signature (R || S)
0x330     336     Reserved
```

The signature is ECDSA P-384:
- R: 72 bytes, little-endian
- S: 72 bytes, little-endian

## Step 2: Extract Components

```bash
WORK_DIR=$(mktemp -d)
REPORT="report.bin"

dd if="$REPORT" of="$WORK_DIR/signed_data.bin" bs=1 count=672
dd if="$REPORT" of="$WORK_DIR/sig_raw.bin" bs=1 skip=672 count=144
dd if="$WORK_DIR/sig_raw.bin" of="$WORK_DIR/r_le.bin" bs=1 count=72
dd if="$WORK_DIR/sig_raw.bin" of="$WORK_DIR/s_le.bin" bs=1 skip=72 count=72
```

## Step 3: Convert Signature to DER Format

AMD stores signatures in little-endian format, but OpenSSL expects big-endian DER format.

```python
#!/usr/bin/env python3
import sys

def le_to_be_48(data):
    be_data = data[::-1]
    first_nonzero = next((i for i, b in enumerate(be_data) if b != 0), len(be_data))
    trimmed = be_data[first_nonzero:]
    if len(trimmed) < 48:
        trimmed = b'\x00' * (48 - len(trimmed)) + trimmed
    return trimmed[-48:]

def to_der_int(data):
    if data[0] & 0x80:
        data = b'\x00' + data
    return bytes([0x02, len(data)]) + data

with open(sys.argv[1], 'rb') as f:
    r_le = f.read()
with open(sys.argv[2], 'rb') as f:
    s_le = f.read()

r_be = le_to_be_48(r_le)
s_be = le_to_be_48(s_le)

r_der = to_der_int(r_be)
s_der = to_der_int(s_be)
seq = r_der + s_der
sig_der = bytes([0x30, len(seq)]) + seq

with open(sys.argv[3], 'wb') as f:
    f.write(sig_der)
```

## Step 4: Extract VCEK Public Key

```bash
openssl x509 -in certs/vcek.pem -pubkey -noout > "$WORK_DIR/vcek_pub.pem"
```

## Step 5: Verify Signature

```bash
openssl dgst -sha384 \
    -verify "$WORK_DIR/vcek_pub.pem" \
    -signature "$WORK_DIR/signature.der" \
    "$WORK_DIR/signed_data.bin"
```

## Verifying Certificate Chain

```bash
# Verify ARK is self-signed
openssl verify -CAfile certs/ark.pem certs/ark.pem

# Verify ASK signed by ARK
openssl verify -CAfile certs/ark.pem certs/ask.pem

# Verify VCEK signed by ASK
cat certs/ark.pem certs/ask.pem > certs/ca_bundle.pem
openssl verify -CAfile certs/ca_bundle.pem certs/vcek.pem
```

## Extracting Report Fields

```bash
# REPORT_DATA (offset 0x50, 64 bytes)
xxd -p -s 80 -l 64 report.bin | fold -w64

# MEASUREMENT (offset 0x90, 48 bytes)
xxd -p -s 144 -l 48 report.bin | tr -d '\n'

# CHIP_ID (offset 0x1A0, 64 bytes)
xxd -p -s 416 -l 64 report.bin | tr -d '\n'
```
MVEOF

cat > /workspace/references/error-codes.md << 'ECEOF'
# SEV-SNP Attestation Error Codes and Troubleshooting

## Chain Verification Errors

### ARK self-signature failed
Re-fetch certificates and verify with: openssl x509 -in certs/ark.pem -text -noout

### VCEK not signed by ASK
Ensure consistent platform (Milan/Genoa). Re-fetch all certificates.

## Report Verification Errors

### Report signature verification failed
Generate fresh report and certificates. Verify VCEK matches chip.

### TCB mismatch
Fetch fresh VCEK with current TCB values.
ECEOF

# Write SKILL.md
cat > /workspace/SKILL.md << 'SKILLEOF'
# sev-attestation

AMD SEV-SNP remote attestation for cryptographic VM identity verification.

## Workflow

1. Detection - Is SEV-SNP available?
2. Generate Report
3. Display Report Info
4. Fetch AMD Certificates (ARK, ASK, VCEK)
5. Verify Cert Chain
6. Verify Report Signature

## Individual Steps

| Script | Purpose |
|--------|---------|
| `scripts/detect-sev-snp.sh` | Check SEV-SNP availability |
| `scripts/generate-report.sh <output_dir>` | Generate attestation report with nonce |
| `scripts/fetch-certificates.sh <report_file> <output_dir>` | Fetch AMD certificates from KDS |
| `scripts/verify-chain.sh <certs_dir>` | Verify certificate chain |
| `scripts/verify-report.sh <report_file> <certs_dir>` | Verify report signature |

## Reference Documentation

- [Report Fields](references/report-fields.md)
- [Error Codes](references/error-codes.md)
- [Manual Verification](references/manual-verification.md)

## Technical Details

- AMD KDS URL: https://kdsintf.amd.com
- Certificate Chain: ARK (self-signed) → ASK → VCEK
- Report Signature: ECDSA P-384
- Device: /dev/sev-guest
SKILLEOF

# Make scripts executable if they exist
chmod -R 755 /workspace/scripts/ 2>/dev/null || true

echo "Setup complete."