#!/usr/bin/env python3
"""
Evaluation script for the Chinese Workdays task.
Checks:
1. data/2027.yaml has been fixed (correct field names, makeup_workdays present)
2. workday_report_2027.json exists and contains required keys
3. The workday counts are mathematically correct per the skill's priority algorithm
"""
import sys
import json
import yaml
from pathlib import Path
from datetime import date, timedelta

def find_file(workspace: Path, filename: str):
    matches = list(workspace.rglob(filename))
    return matches[0] if matches else None

def load_yaml_safe(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def calculate_workdays_reference(start: date, end: date, holidays_data: dict) -> int:
    """Reference implementation of the skill's priority algorithm."""
    makeup_days = set()
    holiday_days = set()

    for h in holidays_data.get("holidays", []):
        for d_str in h.get("makeup_workdays", []):
            makeup_days.add(date.fromisoformat(d_str))
        for d_str in h.get("days_off", []):
            holiday_days.add(date.fromisoformat(d_str))

    count = 0
    current = start
    while current <= end:
        if current in makeup_days:
            count += 1
        elif current in holiday_days:
            pass  # skip
        elif current.weekday() >= 5:  # Saturday=5, Sunday=6
            pass  # skip
        else:
            count += 1
        current += timedelta(days=1)
    return count

def run_checks(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0
    weights = {
        "yaml_field_names_fixed": 0.20,
        "yaml_has_makeup_workdays": 0.15,
        "report_file_exists": 0.05,
        "report_has_required_keys": 0.10,
        "full_year_correct": 0.15,
        "q2_correct": 0.15,
        "april_correct": 0.05,
        "may_correct": 0.05,
        "june_correct": 0.05,
        "custom_range_correct": 0.05,
    }

    # ── CHECK 1: YAML field names fixed ──────────────────────────────────────
    yaml_path = workspace / "data" / "2027.yaml"
    yaml_data = None
    try:
        yaml_data = load_yaml_safe(yaml_path)
        holidays = yaml_data.get("holidays", [])
        # Every holiday must have 'start', 'end', 'days_off' — NOT 'begin/finish/off_days'
        bad_fields = []
        for h in holidays:
            if "begin" in h or "finish" in h or "off_days" in h or "makeup_workday" in h:
                bad_fields.append(h.get("name", "?"))
        passed = len(bad_fields) == 0 and len(holidays) >= 6
        detail = f"Bad field names in: {bad_fields}" if bad_fields else f"All {len(holidays)} holidays have correct field names"
        checks.append({"name": "yaml_field_names_fixed", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["yaml_field_names_fixed"]
    except Exception as e:
        checks.append({"name": "yaml_field_names_fixed", "passed": False, "detail": f"Failed to parse 2027.yaml: {e}"})
        yaml_data = None

    # ── CHECK 2: YAML has makeup_workdays for key holidays ────────────────────
    try:
        assert yaml_data is not None
        holidays = yaml_data.get("holidays", [])
        # At least 2 holidays should have non-empty makeup_workdays
        with_makeup = [h for h in holidays if h.get("makeup_workdays")]
        passed = len(with_makeup) >= 2
        detail = f"{len(with_makeup)} holidays have makeup_workdays defined"
        checks.append({"name": "yaml_has_makeup_workdays", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["yaml_has_makeup_workdays"]
    except Exception as e:
        checks.append({"name": "yaml_has_makeup_workdays", "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 3: Report file exists ───────────────────────────────────────────
    report_path = find_file(workspace, "workday_report_2027.json")
    report_data = None
    if report_path:
        try:
            with open(report_path, encoding="utf-8") as f:
                report_data = json.load(f)
            checks.append({"name": "report_file_exists", "passed": True, "detail": f"Found at {report_path}"})
            total_score += weights["report_file_exists"]
        except Exception as e:
            checks.append({"name": "report_file_exists", "passed": False, "detail": f"File exists but invalid JSON: {e}"})
    else:
        checks.append({"name": "report_file_exists", "passed": False, "detail": "workday_report_2027.json not found"})

    # ── CHECK 4: Report has required keys ─────────────────────────────────────
    REQUIRED_KEYS = ["full_year", "q2", "april", "may", "june", "may10_to_jun30"]
    try:
        assert report_data is not None
        missing = [k for k in REQUIRED_KEYS if k not in report_data]
        passed = len(missing) == 0
        detail = f"Missing keys: {missing}" if missing else "All required keys present"
        checks.append({"name": "report_has_required_keys", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["report_has_required_keys"]
    except Exception as e:
        checks.append({"name": "report_has_required_keys", "passed": False, "detail": f"Cannot check keys: {e}"})

    # ── CHECK 5-10: Verify workday counts using reference algorithm ───────────
    if yaml_data:
        periods = [
            ("full_year",      date(2027, 1, 1),  date(2027, 12, 31)),
            ("q2",             date(2027, 4, 1),  date(2027, 6, 30)),
            ("april",          date(2027, 4, 1),  date(2027, 4, 30)),
            ("may",            date(2027, 5, 1),  date(2027, 5, 31)),
            ("june",           date(2027, 6, 1),  date(2027, 6, 30)),
            ("may10_to_jun30", date(2027, 5, 10), date(2027, 6, 30)),
        ]
        for key, start, end in periods:
            expected = calculate_workdays_reference(start, end, yaml_data)
            try:
                assert report_data is not None
                actual = int(report_data[key])
                # Allow ±1 tolerance for edge cases in makeup workday interpretation
                passed = abs(actual - expected) <= 1
                detail = f"Expected ~{expected}, got {actual}"
                checks.append({"name": f"{key}_correct", "passed": passed, "detail": detail})
                if passed:
                    total_score += weights[f"{key}_correct"]
            except Exception as e:
                checks.append({"name": f"{key}_correct", "passed": False, "detail": f"Could not verify: {e}"})
    else:
        for key in ["full_year", "q2", "april", "may", "june", "may10_to_jun30"]:
            checks.append({"name": f"{key}_correct", "passed": False, "detail": "Cannot compute reference without valid yaml_data"})

    overall_passed = total_score >= 0.70
    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2))