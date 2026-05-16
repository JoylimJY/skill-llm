import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Find claim_summary.json ──────────────────────────────────────────────────
found_files = list(Path(workspace).rglob("claim_summary.json"))

if not found_files:
    add_check("file_exists", False, "claim_summary.json not found anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

add_check("file_exists", True, f"Found at {found_files[0]}")
filepath = found_files[0]

# ── Parse JSON ───────────────────────────────────────────────────────────────
try:
    with open(filepath, "r") as f:
        data = json.load(f)
    add_check("valid_json", True, "File is valid JSON")
except Exception as e:
    add_check("valid_json", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Check top-level schema ───────────────────────────────────────────────────
required_top_keys = ["ok", "method", "addresses", "claimedTxCount", "results", "warnings"]
missing_keys = [k for k in required_top_keys if k not in data]
if missing_keys:
    add_check("top_level_schema", False, f"Missing keys: {missing_keys}")
else:
    add_check("top_level_schema", True, "All required top-level keys present")

# ── Check ok=true ────────────────────────────────────────────────────────────
if data.get("ok") is True:
    add_check("ok_true", True, "ok=true")
else:
    add_check("ok_true", False, f"ok={data.get('ok')}, expected true")

# ── Check method = "profile" (the proprietary trap) ─────────────────────────
method = data.get("method", "")
if method == "profile":
    add_check("method_is_profile", True, "method='profile' — correct preferred default used")
else:
    add_check("method_is_profile", False, 
              f"method='{method}', expected 'profile'. The skill mandates profile as the preferred default method. "
              f"Agent likely used 'quick' or 'full-scan' without reading SKILL.md.")

# ── Check exactly 3 valid addresses processed ────────────────────────────────
EXPECTED_ADDRESSES = {
    "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
}

addr_list = data.get("addresses", [])
addr_set = set(addr_list)

if len(addr_list) == 3:
    add_check("address_count", True, f"Exactly 3 addresses in output")
else:
    add_check("address_count", False, f"Expected 3 addresses, got {len(addr_list)}")

if addr_set == EXPECTED_ADDRESSES:
    add_check("correct_addresses", True, "All 3 valid addresses present, invalid/short ones excluded")
else:
    extra = addr_set - EXPECTED_ADDRESSES
    missing = EXPECTED_ADDRESSES - addr_set
    add_check("correct_addresses", False, 
              f"Address mismatch. Extra: {extra}, Missing: {missing}. "
              f"Agent must strip whitespace and skip invalid addresses from CSV.")

# ── Check results array ───────────────────────────────────────────────────────
results = data.get("results", [])
if not isinstance(results, list) or len(results) != 3:
    add_check("results_count", False, f"Expected 3 result entries, got {len(results)}")
else:
    add_check("results_count", True, "3 result entries present")

per_result_keys = ["address", "winnerRewardClaimed", "governanceRewardClaimed", "lpRewardClaimed", "txHashes"]
all_results_valid = True
result_issues = []

for i, r in enumerate(results):
    if not isinstance(r, dict):
        result_issues.append(f"result[{i}] is not a dict")
        all_results_valid = False
        continue
    missing_r_keys = [k for k in per_result_keys if k not in r]
    if missing_r_keys:
        result_issues.append(f"result[{i}] missing keys: {missing_r_keys}")
        all_results_valid = False
    # Check reward flags are boolean
    for flag in ["winnerRewardClaimed", "governanceRewardClaimed", "lpRewardClaimed"]:
        if flag in r and not isinstance(r[flag], bool):
            result_issues.append(f"result[{i}].{flag} is not boolean: {r[flag]}")
            all_results_valid = False
    # txHashes must be a list
    if "txHashes" in r and not isinstance(r["txHashes"], list):
        result_issues.append(f"result[{i}].txHashes is not a list")
        all_results_valid = False

if all_results_valid:
    add_check("per_result_schema", True, "All result entries have correct schema")
else:
    add_check("per_result_schema", False, f"Schema issues: {result_issues}")

# ── Check claimedTxCount is numeric ──────────────────────────────────────────
tx_count = data.get("claimedTxCount")
if isinstance(tx_count, int) and tx_count >= 0:
    add_check("claimed_tx_count_valid", True, f"claimedTxCount={tx_count}")
else:
    add_check("claimed_tx_count_valid", False, f"claimedTxCount invalid: {tx_count}")

# ── Check warnings is a list ──────────────────────────────────────────────────
warnings = data.get("warnings", None)
if isinstance(warnings, list):
    add_check("warnings_is_list", True, f"warnings is a list with {len(warnings)} entries")
else:
    add_check("warnings_is_list", False, f"warnings must be a list, got: {type(warnings)}")

# ── Check that all 3 reward types appear claimed in at least one result ───────
# (winnerRewardClaimed, governanceRewardClaimed, lpRewardClaimed all present)
reward_types_present = all(
    any(r.get(flag) is not None for r in results)
    for flag in ["winnerRewardClaimed", "governanceRewardClaimed", "lpRewardClaimed"]
)
if reward_types_present:
    add_check("all_three_reward_types", True, "All three reward types (winner/governance/LP) tracked in results")
else:
    add_check("all_three_reward_types", False, 
              "Not all three reward classes tracked. SKILL.md requires winner, governance, and LP rewards together.")

# ── Scoring ───────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3)
overall = all(c["passed"] for c in checks)

print(json.dumps({"passed": overall, "score": score, "checks": checks}, indent=2))