#!/usr/bin/env python3
"""
Evaluation script for the cashu-emoji sandbox task.
Usage: python3 eval_script.py <workspace_dir>

Checks:
1. The output file 'payment_verification.json' exists somewhere in workspace.
2. The JSON contains a 'decoded_token' field starting with 'cashuB'.
3. The JSON contains a 'metadata' object with 'mint', 'unit', 'amount' fields.
4. The metadata mint matches the expected mint URL.
5. The JSON contains a 're_encoded_emoji' field.
6. The re-encoded emoji, when decoded, yields the same token.
7. The re-encoded emoji uses a different carrier (🌰) not the original (🥜).
"""

import sys
import json
import subprocess
import os
from pathlib import Path

def run_decode(text: str, workspace: str) -> dict:
    """Run cashu-emoji decode --metadata --json on the given text."""
    try:
        result = subprocess.run(
            ["node", "/opt/cashu-emoji/bin/cashu-emoji.js", "decode", text, "--metadata", "--json"],
            capture_output=True, text=True, timeout=30
        )
        return {"stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "returncode": result.returncode}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    passed_all = True

    # Load reference data
    ref_path = Path(workspace) / ".eval_ref.json"
    try:
        with open(ref_path) as f:
            ref = json.load(f)
        expected_token = ref["full_token"]
        expected_token_prefix = ref["expected_token_prefix"]
    except Exception as e:
        checks.append({"name": "load_reference", "passed": False, "detail": f"Could not load eval reference: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── Check 1: Output file exists ──────────────────────────────────────────
    found_files = list(Path(workspace).rglob("payment_verification.json"))
    if not found_files:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "payment_verification.json not found anywhere in workspace"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    output_path = found_files[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": str(output_path)})

    # ── Check 2: Valid JSON ──────────────────────────────────────────────────
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        passed_all = False
        print(json.dumps({"passed": False, "score": 0.2, "checks": checks}))
        return

    # ── Check 3: decoded_token field present and correct ─────────────────────
    decoded_token = data.get("decoded_token", "")
    token_ok = isinstance(decoded_token, str) and decoded_token.startswith("cashuB")
    checks.append({
        "name": "decoded_token_present",
        "passed": token_ok,
        "detail": f"decoded_token starts with 'cashuB': {token_ok}. Value prefix: {str(decoded_token)[:60]}"
    })
    if not token_ok:
        passed_all = False

    # Check token matches expected
    token_match = isinstance(decoded_token, str) and decoded_token.strip() == expected_token.strip()
    checks.append({
        "name": "decoded_token_correct",
        "passed": token_match,
        "detail": f"Token matches expected: {token_match}. Got prefix: {str(decoded_token)[:60]}"
    })
    if not token_match:
        passed_all = False

    # ── Check 4: metadata object with correct fields ──────────────────────────
    metadata = data.get("metadata", {})
    has_mint = isinstance(metadata, dict) and "mint" in metadata
    has_unit = isinstance(metadata, dict) and "unit" in metadata
    has_amount = isinstance(metadata, dict) and "amount" in metadata

    checks.append({
        "name": "metadata_fields_present",
        "passed": has_mint and has_unit and has_amount,
        "detail": f"mint={has_mint}, unit={has_unit}, amount={has_amount}. metadata={json.dumps(metadata)}"
    })
    if not (has_mint and has_unit and has_amount):
        passed_all = False

    # Check mint URL
    expected_mint = "https://mint.minibits.cash/Bitcoin"
    mint_val = metadata.get("mint", "") if isinstance(metadata, dict) else ""
    mint_ok = expected_mint in str(mint_val)
    checks.append({
        "name": "metadata_mint_correct",
        "passed": mint_ok,
        "detail": f"Expected mint contains '{expected_mint}', got '{mint_val}'"
    })
    if not mint_ok:
        passed_all = False

    # ── Check 5: re_encoded_emoji field present ───────────────────────────────
    re_encoded = data.get("re_encoded_emoji", "")
    re_encoded_present = isinstance(re_encoded, str) and len(re_encoded) > 0
    checks.append({
        "name": "re_encoded_emoji_present",
        "passed": re_encoded_present,
        "detail": f"re_encoded_emoji field present and non-empty: {re_encoded_present}"
    })
    if not re_encoded_present:
        passed_all = False

    # ── Check 6: Re-encoded emoji decodes back to the same token ─────────────
    if re_encoded_present:
        decode_result = run_decode(re_encoded, workspace)
        decoded_back_raw = decode_result["stdout"]
        # Try to parse as JSON first, else treat as plain text
        try:
            decoded_back_obj = json.loads(decoded_back_raw)
            decoded_back_token = decoded_back_obj.get("text", "")
        except Exception:
            decoded_back_token = decoded_back_raw.strip()

        roundtrip_ok = decoded_back_token.strip() == expected_token.strip()
        checks.append({
            "name": "re_encoded_roundtrip",
            "passed": roundtrip_ok,
            "detail": (f"Re-decoded token matches original: {roundtrip_ok}. "
                       f"Got prefix: {str(decoded_back_token)[:60]}. "
                       f"stderr: {decode_result['stderr'][:100]}")
        })
        if not roundtrip_ok:
            passed_all = False
    else:
        checks.append({
            "name": "re_encoded_roundtrip",
            "passed": False,
            "detail": "Skipped — re_encoded_emoji not present"
        })
        passed_all = False

    # ── Check 7: Re-encoded emoji uses 🌰 not 🥜 ────────────────────────────
    if re_encoded_present:
        uses_chestnut = "🌰" in re_encoded
        uses_peanut = "🥜" in re_encoded
        carrier_ok = uses_chestnut and not uses_peanut
        checks.append({
            "name": "correct_carrier_emoji",
            "passed": carrier_ok,
            "detail": (f"Uses 🌰: {uses_chestnut}, Uses 🥜 (wrong): {uses_peanut}. "
                       f"carrier_ok={carrier_ok}")
        })
        if not carrier_ok:
            passed_all = False
    else:
        checks.append({
            "name": "correct_carrier_emoji",
            "passed": False,
            "detail": "Skipped — re_encoded_emoji not present"
        })
        passed_all = False

    # ── Score ────────────────────────────────────────────────────────────────
    num_checks = len(checks)
    num_passed = sum(1 for c in checks if c["passed"])
    score = round(num_passed / num_checks, 3)

    print(json.dumps({
        "passed": passed_all,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()