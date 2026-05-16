import sys
import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

def parse_dt(s):
    """Parse ISO 8601 datetime string."""
    from dateutil.parser import parse
    return parse(s)

def dt_to_minutes(dt, ref_dt):
    """Convert datetime to minutes since reference."""
    delta = dt - ref_dt
    return delta.total_seconds() / 60

def check_slot_duration_minutes(start_str, end_str):
    s = parse_dt(start_str)
    e = parse_dt(end_str)
    return (e - s).total_seconds() / 60

workspace = sys.argv[1]
checks = []

# ---- Find the output report file ----
report_files = list(Path(workspace).rglob("availability_report.json"))

check_file_exists = {
    "name": "availability_report.json exists",
    "passed": len(report_files) > 0,
    "detail": f"Found {len(report_files)} file(s) named availability_report.json"
}
checks.append(check_file_exists)

if not report_files:
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

report_path = report_files[0]

try:
    with open(report_path) as f:
        report = json.load(f)
except Exception as e:
    checks.append({"name": "Report is valid JSON", "passed": False, "detail": str(e)})
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

checks.append({"name": "Report is valid JSON", "passed": True, "detail": "File parsed successfully"})

# ---- Check: All 4 user open_ids are present in the report ----
report_str = json.dumps(report).lower()
expected_oids = ["ou_a1b2c3d4", "ou_e5f6g7h8", "ou_i9j0k1l2", "ou_m3n4o5p6"]
all_oids_present = all(oid.lower() in report_str for oid in expected_oids)
checks.append({
    "name": "All 4 user open_ids present in report",
    "passed": all_oids_present,
    "detail": f"Expected all of {expected_oids} to appear in report. Found: {[oid for oid in expected_oids if oid.lower() in report_str]}"
})

# ---- Check: freebusy action "list" was used (report references the query window) ----
# The report should cover 2026-07-15 in some form
date_present = "2026-07-15" in json.dumps(report)
checks.append({
    "name": "Report covers 2026-07-15",
    "passed": date_present,
    "detail": "Date 2026-07-15 should appear in the report as the query date"
})

# ---- Check: Correct free slots identified ----
# Ground truth: busy slots merged across all 4 users on 09:00-18:00
# Zhang Wei: 09:30-10:30, 13:00-14:00
# Li Ming: 10:00-11:30, 15:00-16:00
# Wang Fang: 09:00-09:30, 11:00-12:00, 14:30-16:30
# Chen Jun: 10:30-12:00, 16:00-17:00
# All busy merged: 09:00-12:00, 13:00-14:00, 14:30-17:00
# Free windows: 12:00-13:00 (60 min), 14:00-14:30 (30 min), 17:00-18:00 (60 min)
# Only >=90 min free slot: NONE in 09:00-18:00 range
# Wait let me re-verify:
# sorted busy: 
#   WF: 09:00-09:30
#   ZW: 09:30-10:30
#   LM: 10:00-11:30
#   WF: 11:00-12:00  --> merge with LM 10:00-11:30 -> 10:00-12:00
#   CJ: 10:30-12:00  --> absorbed
#   ZW: 13:00-14:00
#   WF: 14:30-16:30
#   LM: 15:00-16:00  --> absorbed
#   CJ: 16:00-17:00  --> merge -> 14:30-17:00
# Merged: 09:00-12:00, 13:00-14:00, 14:30-17:00
# Free: 12:00-13:00 (60min), 14:00-14:30 (30min), 17:00-18:00 (60min)
# 90-min slots: NONE fit exactly, so no 90-min window available

# The report should indicate NO available 90-minute slot exists
report_text = json.dumps(report).lower()

# Check for conflict/no-available-slot indication
no_slot_indicators = ["no available", "no slot", "conflict", "cannot schedule", 
                      "不可用", "冲突", "no 90", "none", "unavailable", "0 slot",
                      "no suitable", "no common", "no free slot"]
has_conflict_note = any(indicator in report_text for indicator in no_slot_indicators)

# Also acceptable: report lists the free slots (12:00-13:00, 14:00-14:30, 17:00-18:00) and notes none >= 90 min
free_slot_12 = "12:00" in report_text and "13:00" in report_text
free_slot_17 = "17:00" in report_text and "18:00" in report_text

conflict_or_slots_present = has_conflict_note or (free_slot_12 and free_slot_17)
checks.append({
    "name": "Report correctly identifies no 90-min available window",
    "passed": conflict_or_slots_present,
    "detail": (
        f"No 90-minute common free slot exists (max free windows: 12:00-13:00=60min, 14:00-14:30=30min, 17:00-18:00=60min). "
        f"Report should indicate this conflict or list these slots. "
        f"Found conflict indicators: {has_conflict_note}, free slot mentions: 12:00-13:00={free_slot_12}, 17:00-18:00={free_slot_17}"
    )
})

# ---- Check: Merged busy slots are correctly computed ----
# Specifically: the 09:00-12:00 merged block should be mentioned
busy_09_12 = ("09:00" in report_text or "9:00" in report_text) and "12:00" in report_text
checks.append({
    "name": "Report reflects merged busy block 09:00-12:00",
    "passed": busy_09_12,
    "detail": "The report should reference the morning busy block from 09:00 to 12:00 (merged from multiple users)"
})

# ---- Check: Free slots listed (at least one of the correct ones) ----
has_valid_free_slot = free_slot_12 or free_slot_17
checks.append({
    "name": "At least one correct free slot (12:00-13:00 or 17:00-18:00) is listed",
    "passed": has_valid_free_slot,
    "detail": f"Expected at least one of: 12:00-13:00 or 17:00-18:00. report has 12-13: {free_slot_12}, 17-18: {free_slot_17}"
})

# ---- Check: Report contains user name mappings ----
names_present = all(name.lower() in report_text for name in ["zhang wei", "li ming", "wang fang", "chen jun"])
checks.append({
    "name": "All 4 team member names present in report",
    "passed": names_present,
    "detail": f"Expected Zhang Wei, Li Ming, Wang Fang, Chen Jun in report"
})

# ---- Scoring ----
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)

# Overall pass requires core logic checks to pass
core_checks = [
    "All 4 user open_ids present in report",
    "Report correctly identifies no 90-min available window",
    "At least one correct free slot (12:00-13:00 or 17:00-18:00) is listed",
]
core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)

result = {
    "passed": core_passed and score >= 0.7,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))