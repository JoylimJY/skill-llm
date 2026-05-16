#!/usr/bin/env python3
"""
Evaluation script for the Base Wallet agent self-registration task.
Checks that the agent correctly:
1. Created a new wallet using the provided scripts
2. Constructed a valid SIWE message with the correct Base Mainnet chain ID (8453)
3. Signed the SIWE message with the wallet's private key
4. Produced a correctly structured agent_registration.json file
"""

import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

def find_registration_file(workspace: str) -> Path | None:
    """Search for agent_registration.json anywhere in the workspace."""
    results = list(Path(workspace).rglob("agent_registration.json"))
    return results[0] if results else None


def run_js_verify(address: str, message: str, signature: str) -> tuple[bool, str]:
    """
    Use node/ethers to verify that the signature on the message recovers to the given address.
    """
    verify_script = f"""
const {{ ethers }} = require('ethers');

async function main() {{
  const message = {json.dumps(message)};
  const signature = {json.dumps(signature)};
  const expectedAddress = {json.dumps(address)};
  
  try {{
    const recovered = ethers.verifyMessage(message, signature);
    const matches = recovered.toLowerCase() === expectedAddress.toLowerCase();
    console.log(JSON.stringify({{
      recovered: recovered,
      expected: expectedAddress,
      matches: matches
    }}));
  }} catch(e) {{
    console.log(JSON.stringify({{error: e.message, matches: false}}));
  }}
}}

main();
"""
    try:
        result = subprocess.run(
            ["node", "-e", verify_script],
            capture_output=True, text=True, timeout=15,
            cwd="/workspace"
        )
        if result.returncode != 0:
            return False, f"Node error: {result.stderr[:200]}"
        data = json.loads(result.stdout.strip())
        if data.get("error"):
            return False, f"Verification error: {data['error']}"
        return data.get("matches", False), f"Recovered: {data.get('recovered', 'unknown')}"
    except Exception as e:
        return False, f"Exception during verification: {str(e)}"


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── Check 1: Output file exists ──────────────────────────────────────────
    reg_file = find_registration_file(workspace)
    check_file_exists = {
        "name": "agent_registration.json exists",
        "passed": reg_file is not None,
        "detail": str(reg_file) if reg_file else "File agent_registration.json not found anywhere in workspace"
    }
    checks.append(check_file_exists)

    if not reg_file:
        output = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(output))
        return

    # ── Load and parse the file ───────────────────────────────────────────────
    try:
        with open(reg_file, "r") as f:
            reg_data = json.load(f)
    except Exception as e:
        checks.append({
            "name": "agent_registration.json is valid JSON",
            "passed": False,
            "detail": f"JSON parse error: {str(e)}"
        })
        output = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(output))
        return

    checks.append({
        "name": "agent_registration.json is valid JSON",
        "passed": True,
        "detail": f"Parsed successfully from {reg_file}"
    })

    # ── Check 2: Required fields present ─────────────────────────────────────
    required_fields = ["agent_address", "siwe_message", "siwe_signature", "registered_at"]
    missing = [f for f in required_fields if f not in reg_data]
    checks.append({
        "name": "All required fields present (agent_address, siwe_message, siwe_signature, registered_at)",
        "passed": len(missing) == 0,
        "detail": f"Missing fields: {missing}" if missing else "All fields present"
    })

    if missing:
        output = {"passed": False, "score": round(1/6, 4), "checks": checks}
        print(json.dumps(output))
        return

    agent_address = reg_data.get("agent_address", "")
    siwe_message = reg_data.get("siwe_message", "")
    siwe_signature = reg_data.get("siwe_signature", "")
    registered_at = reg_data.get("registered_at", "")

    # ── Check 3: Valid Ethereum address format ────────────────────────────────
    addr_pattern = re.compile(r'^0x[a-fA-F0-9]{40}$')
    addr_valid = bool(addr_pattern.match(agent_address))
    checks.append({
        "name": "agent_address has valid Ethereum format (0x + 40 hex chars)",
        "passed": addr_valid,
        "detail": f"Address: {agent_address}"
    })

    # ── Check 4: SIWE message contains correct Chain ID 8453 (Base Mainnet) ──
    chain_id_match = re.search(r'Chain ID:\s*(\d+)', siwe_message)
    correct_chain_id = False
    chain_id_detail = "Chain ID field not found in SIWE message"
    if chain_id_match:
        found_chain_id = int(chain_id_match.group(1))
        correct_chain_id = (found_chain_id == 8453)
        chain_id_detail = f"Found Chain ID: {found_chain_id} (expected 8453)"
    checks.append({
        "name": "SIWE message contains correct Base Mainnet Chain ID (8453)",
        "passed": correct_chain_id,
        "detail": chain_id_detail
    })

    # ── Check 5: SIWE message has all required EIP-4361 fields ───────────────
    siwe_required_fields = {
        "URI": r'URI:\s*https?://',
        "Version": r'Version:\s*1',
        "Nonce": r'Nonce:\s*\w+',
        "Issued At": r'Issued At:\s*\d{4}-\d{2}-\d{2}T',
        "address in header": r'0x[a-fA-F0-9]{40}',
        "domain in header": r'\w+.*wants you to sign in',
    }
    siwe_field_results = {}
    for field_name, pattern in siwe_required_fields.items():
        siwe_field_results[field_name] = bool(re.search(pattern, siwe_message))

    # Also check the specific nonce from task_spec
    expected_nonce = "aB3xK9mN2pQr7vWz"
    nonce_match = re.search(r'Nonce:\s*(\S+)', siwe_message)
    nonce_used = nonce_match.group(1) if nonce_match else None
    nonce_correct = nonce_used == expected_nonce

    all_siwe_present = all(siwe_field_results.values())
    checks.append({
        "name": "SIWE message has all required EIP-4361 fields (URI, Version, Nonce, Issued At, address, domain)",
        "passed": all_siwe_present,
        "detail": f"Field check: {siwe_field_results}"
    })

    checks.append({
        "name": f"SIWE message uses the correct nonce from task_spec.json ({expected_nonce})",
        "passed": nonce_correct,
        "detail": f"Nonce in message: {nonce_used}, expected: {expected_nonce}"
    })

    # ── Check 6: SIWE message contains the agent's address ───────────────────
    addr_in_msg = agent_address.lower() in siwe_message.lower()
    checks.append({
        "name": "SIWE message contains the agent's wallet address",
        "passed": addr_in_msg,
        "detail": f"Address {agent_address} {'found' if addr_in_msg else 'NOT found'} in SIWE message"
    })

    # ── Check 7: Statement matches task spec ──────────────────────────────────
    expected_statement = "I am registering as an autonomous agent on the AutonomousAgentHub platform."
    statement_in_msg = expected_statement in siwe_message
    checks.append({
        "name": "SIWE message contains the required statement from task_spec.json",
        "passed": statement_in_msg,
        "detail": f"Statement {'found' if statement_in_msg else 'NOT found'} in SIWE message"
    })

    # ── Check 8: Signature format is valid (0x + 130 hex chars) ──────────────
    sig_pattern = re.compile(r'^0x[a-fA-F0-9]{130}$')
    sig_valid = bool(sig_pattern.match(siwe_signature))
    checks.append({
        "name": "siwe_signature has valid ECDSA signature format (0x + 130 hex chars)",
        "passed": sig_valid,
        "detail": f"Signature length: {len(siwe_signature)}, expected 132 chars (0x + 130)"
    })

    # ── Check 9: Cryptographic signature verification ─────────────────────────
    sig_ok = False
    sig_detail = "Skipped due to invalid signature format"
    if sig_valid and addr_valid:
        sig_ok, sig_detail = run_js_verify(agent_address, siwe_message, siwe_signature)
    checks.append({
        "name": "Signature cryptographically verifies: recovered address matches agent_address",
        "passed": sig_ok,
        "detail": sig_detail
    })

    # ── Check 10: registered_at is a valid ISO8601 timestamp ─────────────────
    ts_valid = False
    ts_detail = f"Value: {registered_at}"
    try:
        # Accept various ISO8601 formats
        ts_str = registered_at.replace('Z', '+00:00')
        datetime.fromisoformat(ts_str)
        ts_valid = True
        ts_detail = f"Valid ISO8601 timestamp: {registered_at}"
    except Exception as e:
        ts_detail = f"Invalid timestamp '{registered_at}': {e}"
    checks.append({
        "name": "registered_at is a valid ISO8601 timestamp",
        "passed": ts_valid,
        "detail": ts_detail
    })

    # ── Check 11: URI in SIWE matches task spec ───────────────────────────────
    expected_uri = "https://agentplatform.local/register"
    uri_correct = expected_uri in siwe_message
    checks.append({
        "name": f"SIWE message URI matches task_spec.json ({expected_uri})",
        "passed": uri_correct,
        "detail": f"Expected URI '{expected_uri}' {'found' if uri_correct else 'NOT found'} in SIWE message"
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    score = round(passed_count / total_count, 4)

    # Must pass these critical checks to be considered overall passing
    critical_checks = [
        "agent_registration.json exists",
        "All required fields present (agent_address, siwe_message, siwe_signature, registered_at)",
        "SIWE message contains correct Base Mainnet Chain ID (8453)",
        "Signature cryptographically verifies: recovered address matches agent_address",
        "SIWE message has all required EIP-4361 fields (URI, Version, Nonce, Issued At, address, domain)",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = critical_passed and score >= 0.75

    output = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()