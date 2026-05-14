#!/usr/bin/env python3
"""
Evaluation script for SEV-SNP attestation audit task.
Checks:
1. report_fields.json exists with correct field values extracted from binary
2. chain_verification.txt or similar confirms ARK->ASK->VCEK chain is valid
3. signature_verification.txt or similar confirms report signature is valid
4. audit_verdict.json exists with correct security verdict (PASSED, debug_bit=0, etc.)
"""

import sys
import json
import subprocess
import struct
import hashlib
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
passed_all = True

def add_check(name, passed, detail):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# ── Load ground truth ──────────────────────────────────────────────────────
try:
    gt = json.loads(Path("/tmp/eval_ground_truth.json").read_text())
except Exception as e:
    add_check("load_ground_truth", False, f"Could not load ground truth: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Find agent output files ────────────────────────────────────────────────
# Search for report_fields.json
report_fields_files = list(workspace.rglob("report_fields.json"))
audit_verdict_files = list(workspace.rglob("audit_verdict.json"))

# ── CHECK 1: report_fields.json exists ────────────────────────────────────
if not report_fields_files:
    add_check("report_fields_file_exists", False, "No report_fields.json found anywhere in workspace")
else:
    add_check("report_fields_file_exists", True, f"Found at {report_fields_files[0]}")

# ── CHECK 2: report_fields.json has correct VERSION ───────────────────────
if report_fields_files:
    try:
        rf = json.loads(report_fields_files[0].read_text())
        version_val = rf.get("version") or rf.get("VERSION")
        if version_val is not None:
            version_int = int(str(version_val), 0) if isinstance(version_val, str) else int(version_val)
            ok = (version_int == 2)
            add_check("report_version_correct", ok,
                      f"VERSION={version_int}, expected 2")
        else:
            add_check("report_version_correct", False, "No 'version' key in report_fields.json")
    except Exception as e:
        add_check("report_version_correct", False, f"Error reading report_fields.json: {e}")
else:
    add_check("report_version_correct", False, "report_fields.json missing")

# ── CHECK 3: report_fields.json has correct REPORT_DATA ───────────────────
if report_fields_files:
    try:
        rf = json.loads(report_fields_files[0].read_text())
        # Accept various key names
        rd_val = rf.get("report_data") or rf.get("REPORT_DATA") or rf.get("nonce") or rf.get("NONCE")
        expected_hex = gt["report_data_hex"]
        if rd_val is not None:
            agent_hex = str(rd_val).lower().replace(" ", "").replace("\n", "").replace("0x", "")
            expected_clean = expected_hex.lower()
            ok = (agent_hex == expected_clean)
            add_check("report_data_correct", ok,
                      f"REPORT_DATA match: {ok}. Agent: {agent_hex[:32]}... Expected: {expected_clean[:32]}...")
        else:
            add_check("report_data_correct", False, "No 'report_data' key found in report_fields.json")
    except Exception as e:
        add_check("report_data_correct", False, f"Error: {e}")
else:
    add_check("report_data_correct", False, "report_fields.json missing")

# ── CHECK 4: report_fields.json has correct MEASUREMENT ───────────────────
if report_fields_files:
    try:
        rf = json.loads(report_fields_files[0].read_text())
        m_val = rf.get("measurement") or rf.get("MEASUREMENT")
        expected_hex = gt["measurement_hex"]
        if m_val is not None:
            agent_hex = str(m_val).lower().replace(" ", "").replace("\n", "").replace("0x", "")
            ok = (agent_hex == expected_hex.lower())
            add_check("measurement_correct", ok,
                      f"MEASUREMENT match: {ok}. Agent: {agent_hex[:32]}...")
        else:
            add_check("measurement_correct", False, "No 'measurement' key in report_fields.json")
    except Exception as e:
        add_check("measurement_correct", False, f"Error: {e}")
else:
    add_check("measurement_correct", False, "report_fields.json missing")

# ── CHECK 5: report_fields.json has correct CHIP_ID ───────────────────────
if report_fields_files:
    try:
        rf = json.loads(report_fields_files[0].read_text())
        c_val = rf.get("chip_id") or rf.get("CHIP_ID")
        expected_hex = gt["chip_id_hex"]
        if c_val is not None:
            agent_hex = str(c_val).lower().replace(" ", "").replace("\n", "").replace("0x", "")
            ok = (agent_hex == expected_hex.lower())
            add_check("chip_id_correct", ok,
                      f"CHIP_ID match: {ok}")
        else:
            add_check("chip_id_correct", False, "No 'chip_id' key in report_fields.json")
    except Exception as e:
        add_check("chip_id_correct", False, f"Error: {e}")
else:
    add_check("chip_id_correct", False, "report_fields.json missing")

# ── CHECK 6: DEBUG bit correctly identified as 0 ──────────────────────────
if report_fields_files:
    try:
        rf = json.loads(report_fields_files[0].read_text())
        # Accept various representations
        policy_val = rf.get("policy") or rf.get("POLICY")
        debug_val = rf.get("debug_bit") or rf.get("DEBUG") or rf.get("debug") or rf.get("policy_debug")
        ok = False
        detail = ""
        if debug_val is not None:
            # Should be 0/false/False
            if str(debug_val).lower() in ("0", "false", "no", "not set", "disabled"):
                ok = True
            elif isinstance(debug_val, (int, float)) and int(debug_val) == 0:
                ok = True
            detail = f"debug_bit value: {debug_val}"
        elif policy_val is not None:
            # Try to parse policy and check bit 3
            try:
                pv = int(str(policy_val), 0)
                ok = ((pv >> 3) & 1) == 0
                detail = f"policy=0x{pv:x}, debug_bit={(pv>>3)&1}"
            except:
                detail = f"Cannot parse policy: {policy_val}"
        else:
            detail = "No debug_bit or policy field found"
        add_check("debug_bit_is_zero", ok, detail)
    except Exception as e:
        add_check("debug_bit_is_zero", False, f"Error: {e}")
else:
    add_check("debug_bit_is_zero", False, "report_fields.json missing")

# ── CHECK 7: Certificate chain verification ────────────────────────────────
# The agent should have produced some output confirming chain is valid.
# Look for chain_verification result in audit_verdict.json or a separate file
chain_ok = False
chain_detail = "No chain verification result found"

# Check audit_verdict.json first
if audit_verdict_files:
    try:
        av = json.loads(audit_verdict_files[0].read_text())
        chain_result = (av.get("chain_verification") or av.get("cert_chain") or
                        av.get("certificate_chain") or av.get("chain"))
        if chain_result is not None:
            if str(chain_result).upper() in ("PASSED", "OK", "VALID", "TRUE", "SUCCESS"):
                chain_ok = True
                chain_detail = f"chain_verification={chain_result}"
            elif isinstance(chain_result, bool) and chain_result:
                chain_ok = True
                chain_detail = "chain_verification=True"
            else:
                chain_detail = f"chain_verification={chain_result}"
    except Exception as e:
        chain_detail = f"Error reading audit_verdict.json: {e}"

# Also accept a standalone chain verification file
if not chain_ok:
    chain_files = (list(workspace.rglob("chain_verification.txt")) +
                   list(workspace.rglob("cert_chain_result.txt")) +
                   list(workspace.rglob("chain_result.txt")))
    if chain_files:
        try:
            content = chain_files[0].read_text().upper()
            if "OK" in content or "VALID" in content or "PASSED" in content or "VERIFIED OK" in content:
                chain_ok = True
                chain_detail = f"Chain verification file content: {content[:100]}"
        except Exception as e:
            chain_detail = f"Error reading chain file: {e}"

# Independently verify the chain is actually valid using openssl
try:
    certs_dir = workspace / "attestation_package" / "certs"
    ca_bundle = certs_dir / "ca_bundle.pem"
    # Create ca_bundle for eval
    if not ca_bundle.exists():
        with open(ca_bundle, 'wb') as f:
            f.write((certs_dir / "ark.pem").read_bytes())
            f.write((certs_dir / "ask.pem").read_bytes())
    
    result = subprocess.run(
        ["openssl", "verify", "-CAfile", str(ca_bundle), str(certs_dir / "vcek.pem")],
        capture_output=True, text=True
    )
    chain_actually_valid = (result.returncode == 0)
except Exception as e:
    chain_actually_valid = False

if chain_actually_valid:
    add_check("chain_verification_result", chain_ok,
              f"Agent reported chain valid: {chain_ok}. Chain IS actually valid. {chain_detail}")
else:
    add_check("chain_verification_result", False,
              f"Certificate chain is not valid in workspace. {chain_detail}")

# ── CHECK 8: Signature verification result ────────────────────────────────
sig_ok = False
sig_detail = "No signature verification result found"

if audit_verdict_files:
    try:
        av = json.loads(audit_verdict_files[0].read_text())
        sig_result = (av.get("signature_verification") or av.get("report_signature") or
                      av.get("signature") or av.get("sig_verification"))
        if sig_result is not None:
            if str(sig_result).upper() in ("PASSED", "OK", "VALID", "TRUE", "SUCCESS", "VERIFIED OK"):
                sig_ok = True
                sig_detail = f"signature_verification={sig_result}"
            elif isinstance(sig_result, bool) and sig_result:
                sig_ok = True
                sig_detail = "signature_verification=True"
            else:
                sig_detail = f"signature_verification={sig_result}"
    except Exception as e:
        sig_detail = f"Error: {e}"

# Also check standalone sig verification files
if not sig_ok:
    sig_files = (list(workspace.rglob("signature_verification.txt")) +
                 list(workspace.rglob("sig_result.txt")) +
                 list(workspace.rglob("verify_result.txt")))
    if sig_files:
        try:
            content = sig_files[0].read_text().upper()
            if "VERIFIED OK" in content or "VALID" in content or "PASSED" in content:
                sig_ok = True
                sig_detail = f"Sig file content: {content[:100]}"
        except Exception as e:
            sig_detail = f"Error: {e}"

add_check("signature_verification_result", sig_ok, sig_detail)

# ── CHECK 9: audit_verdict.json exists ────────────────────────────────────
if not audit_verdict_files:
    add_check("audit_verdict_file_exists", False, "No audit_verdict.json found")
else:
    add_check("audit_verdict_file_exists", True, f"Found at {audit_verdict_files[0]}")

# ── CHECK 10: Final verdict is PASSED ─────────────────────────────────────
if audit_verdict_files:
    try:
        av = json.loads(audit_verdict_files[0].read_text())
        verdict = av.get("verdict") or av.get("result") or av.get("status") or av.get("final_result")
        if verdict is not None:
            ok = str(verdict).upper() in ("PASSED", "PASS", "VALID", "SUCCESS", "TRUE")
            add_check("final_verdict_passed", ok,
                      f"Verdict: {verdict}")
        else:
            add_check("final_verdict_passed", False, "No 'verdict' key in audit_verdict.json")
    except Exception as e:
        add_check("final_verdict_passed", False, f"Error: {e}")
else:
    add_check("final_verdict_passed", False, "audit_verdict.json missing")

# ── Score calculation ──────────────────────────────────────────────────────
num_checks = len(checks)
num_passed = sum(1 for c in checks if c["passed"])
score = round(num_passed / num_checks, 4) if num_checks > 0 else 0.0
passed_all = (num_passed == num_checks)

print(json.dumps({
    "passed": passed_all,
    "score": score,
    "checks": checks
}, indent=2))