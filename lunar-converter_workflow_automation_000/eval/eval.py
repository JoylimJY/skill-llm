import sys
import json
import subprocess
from pathlib import Path

workspace = sys.argv[1]

checks = []

def run_check(name, fn):
    try:
        passed, detail = fn()
    except Exception as e:
        passed, detail = False, f"Exception: {e}"
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── Helper: call lunar.py to get ground truth ────────────────────────────────
def lunar2solar_gt(year, month, day):
    r = subprocess.run(
        ["python", "scripts/lunar.py", "lunar2solar", str(year), str(month), str(day)],
        capture_output=True, text=True, cwd=workspace
    )
    return json.loads(r.stdout.strip())["result"]

def solar2lunar_gt(year, month, day):
    r = subprocess.run(
        ["python", "scripts/lunar.py", "solar2lunar", str(year), str(month), str(day)],
        capture_output=True, text=True, cwd=workspace
    )
    return json.loads(r.stdout.strip())["result"]

# ── Precompute ground truth for all 10 employees (year 2026) ──────────────────
YEAR = 2026
employees_raw = [
    {"id": "EMP001", "name": "Zhang Wei",  "calendar": "lunar", "month": 1,  "day": 15},
    {"id": "EMP002", "name": "Li Fang",    "calendar": "solar", "month": 3,  "day": 8},
    {"id": "EMP003", "name": "Wang Jing",  "calendar": "lunar", "month": 5,  "day": 5},
    {"id": "EMP004", "name": "Chen Bo",    "calendar": "solar", "month": 7,  "day": 1},
    {"id": "EMP005", "name": "Zhao Min",   "calendar": "lunar", "month": 8,  "day": 15},
    {"id": "EMP006", "name": "Liu Yang",   "calendar": "solar", "month": 10, "day": 3},
    {"id": "EMP007", "name": "Sun Lei",    "calendar": "lunar", "month": 11, "day": 20},
    {"id": "EMP008", "name": "Zhou Xin",  "calendar": "solar", "month": 1,  "day": 25},
    {"id": "EMP009", "name": "Xu Mei",     "calendar": "lunar", "month": 3,  "day": 3},
    {"id": "EMP010", "name": "Gao Peng",   "calendar": "solar", "month": 6,  "day": 18},
]

ground_truth = {}
for emp in employees_raw:
    eid = emp["id"]
    if emp["calendar"] == "lunar":
        solar = lunar2solar_gt(YEAR, emp["month"], emp["day"])
        y, m, d = map(int, solar.split("-"))
        lunar = solar2lunar_gt(y, m, d)
        ground_truth[eid] = {"solar_date": solar, "lunar_date": lunar}
    else:
        solar = f"{YEAR}-{emp['month']:02d}-{emp['day']:02d}"
        lunar = solar2lunar_gt(YEAR, emp["month"], emp["day"])
        ground_truth[eid] = {"solar_date": solar, "lunar_date": lunar}

# ── Find the output file ──────────────────────────────────────────────────────
def find_output():
    candidates = list(Path(workspace).rglob("birthday_schedule_2026.json"))
    return candidates

# CHECK 1: Output file exists
def check_file_exists():
    files = find_output()
    if not files:
        return False, "birthday_schedule_2026.json not found anywhere in workspace"
    return True, f"Found at: {files[0]}"

run_check("output_file_exists", check_file_exists)

# Load the file for subsequent checks
output_data = None
output_path = None
try:
    files = find_output()
    if files:
        output_path = files[0]
        with open(output_path, "r", encoding="utf-8") as f:
            output_data = json.load(f)
except Exception as e:
    pass

# CHECK 2: All 10 employees present
def check_all_employees():
    if output_data is None:
        return False, "Could not load output file"
    # Accept list or dict keyed by ID
    if isinstance(output_data, list):
        ids_found = {e.get("id") for e in output_data if isinstance(e, dict)}
    elif isinstance(output_data, dict):
        # might be {"employees": [...]} or {"EMP001": {...}, ...}
        if "employees" in output_data:
            ids_found = {e.get("id") for e in output_data["employees"] if isinstance(e, dict)}
        else:
            ids_found = set(output_data.keys())
    else:
        return False, f"Unexpected data type: {type(output_data)}"
    
    expected_ids = set(ground_truth.keys())
    missing = expected_ids - ids_found
    if missing:
        return False, f"Missing employees: {missing}"
    return True, f"All 10 employees present"

run_check("all_10_employees_present", check_all_employees)

# Helper to extract employee record by ID
def get_emp_record(eid):
    if output_data is None:
        return None
    if isinstance(output_data, list):
        for e in output_data:
            if isinstance(e, dict) and e.get("id") == eid:
                return e
    elif isinstance(output_data, dict):
        if "employees" in output_data:
            for e in output_data["employees"]:
                if isinstance(e, dict) and e.get("id") == eid:
                    return e
        elif eid in output_data:
            return output_data[eid]
    return None

# CHECK 3: solar_date correctness for all employees
def check_solar_dates():
    if output_data is None:
        return False, "Could not load output file"
    wrong = []
    for eid, gt in ground_truth.items():
        rec = get_emp_record(eid)
        if rec is None:
            wrong.append(f"{eid}: record missing")
            continue
        # Accept solar_date field (various key names tolerated below)
        solar_val = rec.get("solar_date") or rec.get("solar") or rec.get("gregorian_date")
        if solar_val != gt["solar_date"]:
            wrong.append(f"{eid}: expected solar={gt['solar_date']}, got={solar_val}")
    if wrong:
        return False, "; ".join(wrong)
    return True, "All solar dates correct"

run_check("solar_dates_correct", check_solar_dates)

# CHECK 4: lunar_date correctness for all employees
def check_lunar_dates():
    if output_data is None:
        return False, "Could not load output file"
    wrong = []
    for eid, gt in ground_truth.items():
        rec = get_emp_record(eid)
        if rec is None:
            wrong.append(f"{eid}: record missing")
            continue
        lunar_val = rec.get("lunar_date") or rec.get("lunar") or rec.get("chinese_date")
        if lunar_val != gt["lunar_date"]:
            wrong.append(f"{eid}: expected lunar={gt['lunar_date']}, got={lunar_val}")
    if wrong:
        return False, "; ".join(wrong)
    return True, "All lunar dates correct"

run_check("lunar_dates_correct", check_lunar_dates)

# CHECK 5: Bidirectional conversion consistency
# For employees originally in lunar calendar, their solar->lunar round-trip must match
def check_roundtrip_consistency():
    if output_data is None:
        return False, "Could not load output file"
    lunar_employees = ["EMP001", "EMP003", "EMP005", "EMP007", "EMP009"]
    issues = []
    for eid in lunar_employees:
        rec = get_emp_record(eid)
        if rec is None:
            issues.append(f"{eid} missing")
            continue
        solar_val = rec.get("solar_date") or rec.get("solar") or rec.get("gregorian_date")
        lunar_val = rec.get("lunar_date") or rec.get("lunar") or rec.get("chinese_date")
        if not solar_val:
            issues.append(f"{eid} no solar_date")
            continue
        # Verify solar_date is parseable
        try:
            y, m, d = map(int, solar_val.split("-"))
            recomputed_lunar = solar2lunar_gt(y, m, d)
            if recomputed_lunar != lunar_val:
                issues.append(f"{eid}: solar {solar_val} -> lunar {recomputed_lunar} != stored {lunar_val}")
        except Exception as e:
            issues.append(f"{eid}: parse error {e}")
    if issues:
        return False, "; ".join(issues)
    return True, "Round-trip consistency verified for all lunar-origin employees"

run_check("roundtrip_consistency", check_roundtrip_consistency)

# ── Score ─────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)

result = {
    "passed": all(c["passed"] for c in checks),
    "score": score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))