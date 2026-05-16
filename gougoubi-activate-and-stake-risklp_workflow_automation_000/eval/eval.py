import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
passed_all = True

def add_check(name, passed, detail):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# ── 1. Find the output file activation_result.json ──────────────────────────
result_files = list(Path(workspace).rglob("activation_result.json"))
if not result_files:
    add_check("output_file_exists", False, "activation_result.json not found anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

result_path = result_files[0]
add_check("output_file_exists", True, f"Found at {result_path}")

# ── 2. Parse the JSON ────────────────────────────────────────────────────────
try:
    with open(result_path) as f:
        result = json.load(f)
    add_check("output_valid_json", True, "Parsed successfully")
except Exception as e:
    add_check("output_valid_json", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── 3. Top-level ok flag ─────────────────────────────────────────────────────
ok_val = result.get("ok")
add_check("result_ok_true", ok_val is True, f"ok={ok_val!r} (expected True)")

# ── 4. Not a dry-run result ──────────────────────────────────────────────────
is_dry = result.get("dryRun", False)
add_check("not_dry_run_output", not is_dry, f"dryRun={is_dry!r} (result must be from live run, not --dry-run)")

# ── 5. Correct proposal address ─────────────────────────────────────────────
EXPECTED_PROPOSAL = "0x1A2B3C4D5E6F7A8B9C0D1E2F3A4B5C6D7E8F9A0B"
got_addr = result.get("proposalAddress", "")
add_check(
    "correct_proposal_address",
    got_addr == EXPECTED_PROPOSAL,
    f"proposalAddress={got_addr!r} (expected {EXPECTED_PROPOSAL!r})"
)

# ── 6. Scope is only-created ─────────────────────────────────────────────────
got_scope = result.get("scope", "")
add_check(
    "scope_only_created",
    got_scope == "only-created",
    f"scope={got_scope!r} (expected 'only-created')"
)

# ── 7. riskLpPerCondition is 150 ─────────────────────────────────────────────
got_lp = str(result.get("riskLpPerCondition", ""))
add_check(
    "risk_lp_amount_150",
    got_lp == "150",
    f"riskLpPerCondition={got_lp!r} (expected '150')"
)

# ── 8. activatedCount == 2 (the two CREATED conditions) ──────────────────────
got_act_count = result.get("activatedCount", -1)
add_check(
    "activated_count_2",
    got_act_count == 2,
    f"activatedCount={got_act_count!r} (expected 2; scope=only-created targets 2 CREATED conditions)"
)

# ── 9. riskLpAddedCount == 2 ─────────────────────────────────────────────────
got_lp_count = result.get("riskLpAddedCount", -1)
add_check(
    "risk_lp_added_count_2",
    got_lp_count == 2,
    f"riskLpAddedCount={got_lp_count!r} (expected 2)"
)

# ── 10. activated list has exactly 2 entries ──────────────────────────────────
activated_list = result.get("activated", [])
add_check(
    "activated_list_length_2",
    isinstance(activated_list, list) and len(activated_list) == 2,
    f"len(activated)={len(activated_list) if isinstance(activated_list, list) else 'N/A'} (expected 2)"
)

# ── 11. riskLpAdded list has exactly 2 entries ────────────────────────────────
lp_added_list = result.get("riskLpAdded", [])
add_check(
    "lp_added_list_length_2",
    isinstance(lp_added_list, list) and len(lp_added_list) == 2,
    f"len(riskLpAdded)={len(lp_added_list) if isinstance(lp_added_list, list) else 'N/A'} (expected 2)"
)

# ── 12. Separate failure arrays exist (schema compliance) ────────────────────
has_act_failed = "activationFailed" in result and isinstance(result["activationFailed"], list)
has_lp_failed = "riskLpFailed" in result and isinstance(result["riskLpFailed"], list)
add_check(
    "separate_failure_arrays_present",
    has_act_failed and has_lp_failed,
    f"activationFailed present={has_act_failed}, riskLpFailed present={has_lp_failed}"
)

# ── 13. dry-run was called before the live run (call log check) ──────────────
log_path = Path(workspace) / "cache/.artifacts/call_log.json"
try:
    with open(log_path) as f:
        call_log = json.load(f)
    calls = call_log.get("calls", [])
    dry_run_calls = [c for c in calls if c.get("isDryRun") is True]
    live_calls = [c for c in calls if c.get("isDryRun") is False]

    dry_before_live = False
    if dry_run_calls and live_calls:
        first_dry = min(c["timestamp"] for c in dry_run_calls)
        first_live = min(c["timestamp"] for c in live_calls)
        dry_before_live = first_dry <= first_live

    add_check(
        "dry_run_called_before_live",
        dry_before_live,
        f"dry_run_calls={len(dry_run_calls)}, live_calls={len(live_calls)}, dry_before_live={dry_before_live}"
    )
except Exception as e:
    add_check("dry_run_called_before_live", False, f"Could not read call log: {e}")

# ── 14. Live call used the correct proposal address ───────────────────────────
try:
    live_correct_addr = any(
        c.get("proposalAddress") == EXPECTED_PROPOSAL and not c.get("isDryRun")
        for c in calls
    )
    add_check(
        "live_call_correct_proposal",
        live_correct_addr,
        f"At least one live call used the correct proposalAddress"
    )
except Exception as e:
    add_check("live_call_correct_proposal", False, f"Error checking call log: {e}")

# ── Score ─────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)

print(json.dumps({
    "passed": passed_all,
    "score": score,
    "checks": checks
}, indent=2))