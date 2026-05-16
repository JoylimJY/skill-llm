import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Find the report file ──────────────────────────────────────────────────
    report_path = None
    candidates = list(Path(workspace).rglob("weekly_health_report.json"))
    if candidates:
        report_path = candidates[0]

    score = add_check(
        "report_file_exists",
        report_path is not None,
        f"Found at {report_path}" if report_path else "weekly_health_report.json not found anywhere in workspace",
        weight=1.0
    )
    total_score += score

    if report_path is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    # ── Load the report ───────────────────────────────────────────────────────
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        total_score += add_check("report_valid_json", True, "File is valid JSON", weight=1.0)
    except Exception as e:
        total_score += add_check("report_valid_json", False, f"JSON parse error: {e}", weight=1.0)
        return {"passed": False, "score": total_score / 10.0, "checks": checks}

    # ── Check 1: Date range covers March 1–7, 2026 ───────────────────────────
    report_str = json.dumps(report).lower()
    has_march_dates = (
        "2026-03-01" in json.dumps(report) or "2026-03" in json.dumps(report)
    )
    total_score += add_check(
        "covers_march_2026_week",
        has_march_dates,
        "Report references March 2026 data" if has_march_dates else "No March 2026 dates found in report",
        weight=1.0
    )

    # ── Check 2: Recovery scores present (7 days worth) ──────────────────────
    # Expected: recovery scores from recovery_calculations
    # Values: [65.2, 58.7, 72.1, 51.3, 68.4, 76.3, 70.5]
    expected_recovery_scores = {65.2, 58.7, 72.1, 51.3, 68.4, 76.3, 70.5}
    report_flat = json.dumps(report)
    found_recovery = sum(1 for v in expected_recovery_scores if str(v) in report_flat or f"{v:.1f}" in report_flat)
    recovery_ok = found_recovery >= 5  # at least 5 of 7 days present
    total_score += add_check(
        "recovery_scores_from_recovery_calculations",
        recovery_ok,
        f"Found {found_recovery}/7 expected recovery scores (65.2, 58.7, 72.1, 51.3, 68.4, 76.3, 70.5)",
        weight=2.0
    )

    # ── Check 3: Sleep debt data from sleep_calculations ─────────────────────
    # Expected sleep_debt values: [-25, -45, 10, -60, -5, 30, 5]
    expected_sleep_debt = {-25, -45, 10, -60, -5, 30, 5}
    found_debt = sum(1 for v in expected_sleep_debt if str(v) in report_flat)
    sleep_debt_ok = found_debt >= 4  # at least 4 of 7
    total_score += add_check(
        "sleep_debt_from_sleep_calculations",
        sleep_debt_ok,
        f"Found {found_debt}/7 expected sleep_debt values (-25,-45,10,-60,-5,30,5)",
        weight=2.0
    )

    # ── Check 4: HRV data present ─────────────────────────────────────────────
    # HRV values from recovery_calculations: [45.2, 41.8, 48.3, 38.9, 43.1, 50.7, 42.5]
    expected_hrv = {45.2, 41.8, 48.3, 38.9, 43.1, 50.7, 42.5}
    found_hrv = sum(1 for v in expected_hrv if str(v) in report_flat)
    hrv_ok = found_hrv >= 4
    total_score += add_check(
        "hrv_data_present",
        hrv_ok,
        f"Found {found_hrv}/7 HRV values from recovery_calculations",
        weight=1.5
    )

    # ── Check 5: HRV vs baseline comparison present ───────────────────────────
    # HRV baseline is 44.0 — the report must reference this or discuss it
    hrv_baseline_present = (
        "44.0" in report_flat or "44" in report_flat or
        "baseline" in report_str or "hrv_baseline" in report_str
    )
    total_score += add_check(
        "hrv_vs_baseline_analysis",
        hrv_baseline_present,
        "Report includes HRV baseline comparison (baseline=44.0)" if hrv_baseline_present else "No HRV baseline comparison found",
        weight=1.0
    )

    # ── Check 6: Sleep scores from sleep_calculations ─────────────────────────
    # overall_score values: [72.5, 68.1, 78.3, 62.4, 74.0, 80.2, 75.1]
    expected_sleep_scores = {72.5, 68.1, 78.3, 62.4, 74.0, 80.2, 75.1}
    found_sleep_sc = sum(1 for v in expected_sleep_scores if str(v) in report_flat)
    sleep_score_ok = found_sleep_sc >= 4
    total_score += add_check(
        "sleep_scores_from_sleep_calculations",
        sleep_score_ok,
        f"Found {found_sleep_sc}/7 sleep overall_score values (72.5,68.1,78.3,62.4,74.0,80.2,75.1)",
        weight=1.5
    )

    # ── Check 7: Multi-table synthesis — both sleep AND recovery data ─────────
    has_sleep_data = sleep_score_ok or sleep_debt_ok
    has_recovery_data = recovery_ok or hrv_ok
    multi_table = has_sleep_data and has_recovery_data
    total_score += add_check(
        "multi_table_synthesis",
        multi_table,
        "Report synthesizes data from both sleep and recovery tables" if multi_table else "Report only covers one data domain",
        weight=1.0
    )

    # ── Check 8: Structural completeness — report has meaningful keys ─────────
    if isinstance(report, dict):
        meaningful_keys = len([k for k in report.keys() if len(str(k)) > 2])
        struct_ok = meaningful_keys >= 2
    elif isinstance(report, list) and len(report) > 0:
        struct_ok = True
        meaningful_keys = len(report)
    else:
        struct_ok = False
        meaningful_keys = 0
    total_score += add_check(
        "report_has_structure",
        struct_ok,
        f"Report has {meaningful_keys} top-level keys/entries",
        weight=0.5
    )

    # ── Normalize score ───────────────────────────────────────────────────────
    max_score = 1.0 + 1.0 + 2.0 + 2.0 + 1.5 + 1.0 + 1.5 + 1.0 + 0.5  # = 11.5
    normalized = round(total_score / max_score, 3)
    passed = normalized >= 0.65 and checks[0]["passed"] and checks[1]["passed"]

    return {
        "passed": passed,
        "score": normalized,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg_error", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))