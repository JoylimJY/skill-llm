import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0
total_checks = 6

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# --- Load call history ---
call_history_path = Path(workspace) / "tmp" / "call_history.jsonl"
call_history = []
try:
    with open(call_history_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                call_history.append(json.loads(line))
except Exception as e:
    add_check("call_history_readable", False, f"Could not read call history: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# --- CHECK 1: auth_status was called ---
auth_calls = [c for c in call_history if c.get("action") == "auth_status"]
if auth_calls:
    add_check("auth_status_called", True, f"auth_status was invoked {len(auth_calls)} time(s).")
    score += 1
else:
    add_check("auth_status_called", False, "auth_status was never called via request.js.")

# --- CHECK 2: latest_recovery was called with correct defaults or explicit values ---
rec_calls = [c for c in call_history if c.get("action") == "latest_recovery"]
if rec_calls:
    # Accept: called with no days override (None → default 3) OR explicitly days=3
    valid_rec = any(
        (c.get("days") is None or c.get("days") == 3)
        for c in rec_calls
    )
    if valid_rec:
        add_check("latest_recovery_correct_params", True, f"latest_recovery called with correct days (3 or default). Calls: {rec_calls}")
        score += 1
    else:
        add_check("latest_recovery_correct_params", False, f"latest_recovery called but with wrong days override. Calls: {rec_calls}")
else:
    add_check("latest_recovery_correct_params", False, "latest_recovery was never called via request.js.")

# --- CHECK 3: training_window was called with days=21 (non-default, as required by prompt) ---
tw_calls = [c for c in call_history if c.get("action") == "training_window"]
if tw_calls:
    valid_tw = any(c.get("days") == 21 for c in tw_calls)
    if valid_tw:
        add_check("training_window_21_days", True, f"training_window called with days=21 as required. Calls: {tw_calls}")
        score += 1
    else:
        add_check("training_window_21_days", False, f"training_window was called but NOT with days=21. Calls: {tw_calls}")
else:
    add_check("training_window_21_days", False, "training_window was never called via request.js.")

# --- CHECK 4: unified_latest called with source='garmin' ---
ul_calls = [c for c in call_history if c.get("action") == "unified_latest"]
if ul_calls:
    valid_ul = any(c.get("source") == "garmin" for c in ul_calls)
    if valid_ul:
        add_check("unified_latest_garmin_source", True, f"unified_latest called with source='garmin'. Calls: {ul_calls}")
        score += 1
    else:
        add_check("unified_latest_garmin_source", False, f"unified_latest was called but NOT with source='garmin'. Calls: {ul_calls}")
else:
    add_check("unified_latest_garmin_source", False, "unified_latest was never called via request.js.")

# --- CHECK 5: health_snapshot.json exists and is valid JSON ---
snapshot_files = list(Path(workspace).rglob("health_snapshot.json"))
# Exclude the archive distractor
snapshot_files = [f for f in snapshot_files if "archive" not in str(f)]

if not snapshot_files:
    add_check("health_snapshot_exists", False, "health_snapshot.json not found in workspace (excluding archive).")
    print(json.dumps({"passed": False, "score": score / total_checks, "checks": checks}))
    sys.exit(0)

snapshot_path = snapshot_files[0]
try:
    with open(snapshot_path, "r") as f:
        snapshot = json.load(f)
    add_check("health_snapshot_exists", True, f"health_snapshot.json found at {snapshot_path} and is valid JSON.")
    score += 1
except Exception as e:
    add_check("health_snapshot_exists", False, f"health_snapshot.json found but could not parse: {e}")
    print(json.dumps({"passed": False, "score": score / total_checks, "checks": checks}))
    sys.exit(0)

# --- CHECK 6: health_snapshot.json contains data from all required sections ---
required_sections_found = []
missing_sections = []

# Must have auth-related data
has_auth = any(
    k in snapshot for k in ["auth", "auth_status", "authentication", "token_valid", "status"]
) or any(
    isinstance(v, dict) and any(k2 in v for k2 in ["token_valid", "authenticated", "user", "status", "expires_in_seconds"])
    for v in snapshot.values() if isinstance(v, dict)
)

# Must have recovery data
has_recovery = any(
    k in snapshot for k in ["recovery", "latest_recovery", "hrv", "records"]
) or any(
    isinstance(v, dict) and any(k2 in v for k2 in ["hrv_rmssd", "resting_hr", "sleep_score", "records"])
    for v in snapshot.values() if isinstance(v, dict)
) or any(
    isinstance(v, list) for v in snapshot.values()
)

# Must have training window data (21-day)
has_training = any(
    k in snapshot for k in ["training_window", "training", "window", "sessions", "load"]
) or any(
    isinstance(v, dict) and any(k2 in v for k2 in ["sessions", "window_days", "load_trend", "days"])
    for v in snapshot.values() if isinstance(v, dict)
)

# Must have unified latest (garmin source)
has_unified = any(
    k in snapshot for k in ["unified", "unified_latest", "readiness", "load_7d"]
) or any(
    isinstance(v, dict) and any(k2 in v for k2 in ["readiness", "load_7d", "load_28d", "source"])
    for v in snapshot.values() if isinstance(v, dict)
)

if has_auth:
    required_sections_found.append("auth")
else:
    missing_sections.append("auth_status")

if has_recovery:
    required_sections_found.append("latest_recovery")
else:
    missing_sections.append("latest_recovery")

if has_training:
    required_sections_found.append("training_window")
else:
    missing_sections.append("training_window(21d)")

if has_unified:
    required_sections_found.append("unified_latest(garmin)")
else:
    missing_sections.append("unified_latest(garmin)")

all_present = len(missing_sections) == 0
if all_present:
    add_check("snapshot_contains_all_sections", True,
              f"health_snapshot.json contains all required sections: {required_sections_found}")
    score += 1
else:
    add_check("snapshot_contains_all_sections", False,
              f"health_snapshot.json missing sections: {missing_sections}. Found: {required_sections_found}. Keys: {list(snapshot.keys())}")

# --- Final result ---
final_score = score / total_checks
passed = score >= (total_checks * 0.85)  # Must pass at least 5/6 checks

print(json.dumps({
    "passed": passed,
    "score": round(final_score, 4),
    "checks": checks
}))