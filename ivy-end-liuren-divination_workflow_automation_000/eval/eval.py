import sys
import json
import subprocess
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
passed_all = True

def add_check(name, passed, detail):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# --- Find the output report ---
report_path = None
candidates = list(Path(workspace).rglob("divination_report.json"))
if candidates:
    report_path = candidates[0]

if not report_path or not report_path.exists():
    add_check("output_file_exists", False, "divination_report.json not found anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)
else:
    add_check("output_file_exists", True, f"Found at {report_path}")

# --- Load and parse report ---
try:
    with open(report_path) as f:
        report = json.load(f)
    add_check("valid_json", True, "Report is valid JSON")
except Exception as e:
    add_check("valid_json", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# --- Check it's a list/array of 4 results ---
if isinstance(report, list):
    entries = report
elif isinstance(report, dict) and any(isinstance(v, list) for v in report.values()):
    # Allow {"results": [...]} style
    for v in report.values():
        if isinstance(v, list):
            entries = v
            break
else:
    entries = [report]

add_check("has_four_entries", len(entries) == 4, f"Expected 4 entries, got {len(entries)}")

# --- Now verify each entry by running liuren.js directly and comparing ---
BATCH = [
    {"id": "REQ-001", "datetime": "2025-03-15 09:00:00"},
    {"id": "REQ-002", "datetime": "2025-07-07 23:30:00"},
    {"id": "REQ-003", "datetime": "2025-11-01 00:45:00"},
    {"id": "REQ-004", "datetime": "2025-06-21 14:30:00"},
]

liuren_path = os.path.join(workspace, "liuren.js")

def run_liuren(datetime_str):
    """Run liuren.js with a given datetime and return parsed JSON output."""
    result = subprocess.run(
        ["node", liuren_path, datetime_str],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        raise RuntimeError(f"liuren.js failed: {result.stderr}")
    return json.loads(result.stdout)

# Compute expected outputs
expected_outputs = {}
for req in BATCH:
    try:
        out = run_liuren(req["datetime"])
        expected_outputs[req["id"]] = out
    except Exception as e:
        add_check(f"reference_run_{req['id']}", False, f"Could not run liuren.js for reference: {e}")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        sys.exit(0)

# --- Verify each expected result appears in the agent's report ---
# Build a lookup from agent report
def find_entry_for_id(entries, req_id):
    """Try to find the entry corresponding to a request ID."""
    for e in entries:
        if isinstance(e, dict):
            # Check direct id field
            if e.get("id") == req_id:
                return e
            # Check nested
            for v in e.values():
                if isinstance(v, dict) and v.get("id") == req_id:
                    return v
    return None

def extract_palace_names(entry):
    """Extract month/day/hour palace names from an entry dict, handling nesting."""
    # Try direct sequence key
    seq = None
    if "sequence" in entry:
        seq = entry["sequence"]
    else:
        for v in entry.values():
            if isinstance(v, dict) and "month_palace" in v:
                seq = v
                break
            if isinstance(v, dict) and "sequence" in v:
                seq = v["sequence"]
                break
    if seq is None:
        return None
    
    mp = seq.get("month_palace", {})
    dp = seq.get("day_palace", {})
    hp = seq.get("hour_palace", {})
    return {
        "month_palace_name": mp.get("name", ""),
        "day_palace_name": dp.get("name", ""),
        "hour_palace_name": hp.get("name", ""),
        "hour_palace_meaning": hp.get("meaning", ""),
    }

correct_count = 0
for req_id, expected in expected_outputs.items():
    exp_seq = expected.get("sequence", {})
    exp_mp = exp_seq.get("month_palace", {}).get("name", "")
    exp_dp = exp_seq.get("day_palace", {}).get("name", "")
    exp_hp = exp_seq.get("hour_palace", {}).get("name", "")
    exp_hm = exp_seq.get("hour_palace", {}).get("meaning", "")
    exp_branch = expected.get("target_time", {}).get("earthly_branch", "")
    exp_lunar = expected.get("target_time", {}).get("lunar_approx", "")

    entry = find_entry_for_id(entries, req_id)
    
    # If not found by ID, try positional (order matters)
    if entry is None:
        idx = BATCH.index(next(r for r in BATCH if r["id"] == req_id))
        if idx < len(entries):
            entry = entries[idx]
    
    if entry is None:
        add_check(f"entry_{req_id}_found", False, f"No entry found for {req_id}")
        continue

    names = extract_palace_names(entry)
    if names is None:
        add_check(f"entry_{req_id}_structure", False, f"Cannot extract palace sequence from entry for {req_id}")
        continue

    # Check all three palaces
    mp_ok = names["month_palace_name"] == exp_mp
    dp_ok = names["day_palace_name"] == exp_dp
    hp_ok = names["hour_palace_name"] == exp_hp
    hm_ok = names["hour_palace_meaning"] == exp_hm

    all_ok = mp_ok and dp_ok and hp_ok and hm_ok
    detail = (
        f"month_palace: got='{names['month_palace_name']}' exp='{exp_mp}' {'OK' if mp_ok else 'FAIL'} | "
        f"day_palace: got='{names['day_palace_name']}' exp='{exp_dp}' {'OK' if dp_ok else 'FAIL'} | "
        f"hour_palace: got='{names['hour_palace_name']}' exp='{exp_hp}' {'OK' if hp_ok else 'FAIL'} | "
        f"meaning_match: {'OK' if hm_ok else 'FAIL'} (lunar expected: {exp_lunar}, branch: {exp_branch})"
    )
    add_check(f"divination_correct_{req_id}", all_ok, detail)
    if all_ok:
        correct_count += 1

# Special check: midnight edge case (REQ-003: 00:45 -> Zi hour, index=1, not index=0)
req3_expected = expected_outputs.get("REQ-003", {})
branch_003 = req3_expected.get("target_time", {}).get("earthly_branch", "")
zi_correct = "子" in branch_003
add_check(
    "midnight_zi_hour_edge_case",
    zi_correct,
    f"REQ-003 (00:45) must map to Zi (子) hour. Got branch: '{branch_003}'"
)

# Special check: REQ-002 (23:30) also maps to Zi
req2_expected = expected_outputs.get("REQ-002", {})
branch_002 = req2_expected.get("target_time", {}).get("earthly_branch", "")
zi_correct_002 = "子" in branch_002
add_check(
    "late_night_23h_zi_hour_edge_case",
    zi_correct_002,
    f"REQ-002 (23:30) must map to Zi (子) hour. Got branch: '{branch_002}'"
)

score = round(correct_count / 4.0, 2)
final_passed = passed_all and correct_count == 4

print(json.dumps({"passed": final_passed, "score": score, "checks": checks}, ensure_ascii=False, indent=2))