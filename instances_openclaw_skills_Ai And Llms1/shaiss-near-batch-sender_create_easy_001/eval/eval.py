import json
import os
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        return None, str(e)

# Check 1: nft_batch.json exists and contains expected marker / structure
try:
    p = workspace / "nft_batch.json"
    if not p.exists():
        add_check("nft_batch_exists", False, "nft_batch.json is missing")
        batch = None
    else:
        try:
            batch = json.loads(p.read_text(encoding='utf-8'))
            marker_ok = "marker" in batch and "near_batch_nft_marker" in str(batch.get("marker", "")).lower()
            transfers = batch.get("transfers", []) if isinstance(batch, dict) else []
            structure_ok = isinstance(transfers, list) and len(transfers) == 3
            add_check("nft_batch_exists", True, "nft_batch.json found")
            add_check("nft_batch_structure", marker_ok and structure_ok, f"marker_ok={marker_ok}, transfer_count={len(transfers) if isinstance(transfers, list) else 'n/a'}")
        except Exception as e:
            add_check("nft_batch_parse", False, f"Could not parse nft_batch.json: {e}")
            batch = None
except Exception as e:
    add_check("nft_batch_overall", False, f"Unexpected error: {e}")

# Check 2: nft_estimate.json exists and mirrors batch content loosely
try:
    p = workspace / "nft_estimate.json"
    if not p.exists():
        add_check("nft_estimate_exists", False, "nft_estimate.json is missing")
        est = None
    else:
        try:
            est = json.loads(p.read_text(encoding='utf-8'))
            marker_ok = "marker" in est and "near_batch_nft_marker" in str(est.get("marker", "")).lower()
            transfers = est.get("transfers", []) if isinstance(est, dict) else []
            add_check("nft_estimate_exists", True, "nft_estimate.json found")
            add_check("nft_estimate_structure", marker_ok and isinstance(transfers, list) and len(transfers) == 3, f"marker_ok={marker_ok}, transfer_count={len(transfers) if isinstance(transfers, list) else 'n/a'}")
        except Exception as e:
            add_check("nft_estimate_parse", False, f"Could not parse nft_estimate.json: {e}")
            est = None
except Exception as e:
    add_check("nft_estimate_overall", False, f"Unexpected error: {e}")

# Check 3: recipient/account fields are fuzzy-matched
try:
    expected_accounts = {"bob.near", "carol.near", "dave.near"}
    expected_token_ids = {"101", "102", "103"}
    expected_contract = "coolnft.near"
    found_accounts = set()
    found_tokens = set()
    contracts_ok = True
    source = None
    if 'batch' in locals() and isinstance(batch, dict):
        source = batch
    elif 'est' in locals() and isinstance(est, dict):
        source = est
    if isinstance(source, dict):
        for item in source.get("transfers", []):
            try:
                found_accounts.add(str(item.get("receiver", "")).strip().lower())
                found_tokens.add(str(item.get("token_id", "")).strip())
                if str(item.get("contract", "")).strip().lower() != expected_contract:
                    contracts_ok = False
            except Exception:
                contracts_ok = False
    accounts_ok = expected_accounts.issubset(found_accounts)
    tokens_ok = expected_token_ids.issubset(found_tokens)
    add_check("nft_fields_match", accounts_ok and tokens_ok and contracts_ok, f"accounts_ok={accounts_ok}, tokens_ok={tokens_ok}, contracts_ok={contracts_ok}")
except Exception as e:
    add_check("nft_fields_match", False, f"Unexpected error: {e}")

passed_count = sum(1 for c in checks if c["passed"])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result))
