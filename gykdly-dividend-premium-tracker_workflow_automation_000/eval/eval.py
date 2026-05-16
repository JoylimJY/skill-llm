#!/usr/bin/env python3
"""
Evaluation script for dividend-premium-tracker task.
Checks:
1. Backfill was run and data file exists with correct date range
2. Premium calculation is correct (dividend_yield - bond_yield)
3. Excel report was generated
4. Monitor was run and alerts.json exists
5. Bond yield 3-consecutive-day rise alert was triggered
6. Premium < 1% alert was triggered
7. Alert count and content match expectations
"""
import sys
import json
import math
from pathlib import Path

def load_json(path: Path):
    with open(path) as f:
        return json.load(f)

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    base = workspace / "dividend-premium-tracker"
    assets = base / "assets"

    checks = []
    total_score = 0.0
    max_score = 7

    # ── Check 1: Data file exists ──────────────────────────────────────────
    data_file = assets / "dividend_premium_data.json"
    check1_passed = False
    check1_detail = ""
    try:
        if data_file.exists():
            data = load_json(data_file)
            check1_passed = len(data) > 0
            check1_detail = f"Data file exists with {len(data)} records."
        else:
            check1_detail = f"Data file not found at {data_file}"
    except Exception as e:
        check1_detail = f"Error reading data file: {e}"
    checks.append({"name": "data_file_exists_with_records", "passed": check1_passed, "detail": check1_detail})
    if check1_passed:
        total_score += 1

    # ── Check 2: Backfill date range covered (2026-01-14 to 2026-03-10) ───
    check2_passed = False
    check2_detail = ""
    try:
        data = load_json(data_file)
        dates = sorted(data.keys())
        has_jan = any(d.startswith("2026-01") for d in dates)
        has_feb = any(d.startswith("2026-02") for d in dates)
        has_mar = any(d.startswith("2026-03") for d in dates)
        check2_passed = has_jan and has_feb and has_mar
        check2_detail = (
            f"Dates span: {dates[0] if dates else 'N/A'} to {dates[-1] if dates else 'N/A'}. "
            f"Jan={has_jan}, Feb={has_feb}, Mar={has_mar}. Total records: {len(dates)}"
        )
    except Exception as e:
        check2_detail = f"Error checking date range: {e}"
    checks.append({"name": "backfill_date_range_covered", "passed": check2_passed, "detail": check2_detail})
    if check2_passed:
        total_score += 1

    # ── Check 3: Premium calculation is correct ────────────────────────────
    check3_passed = False
    check3_detail = ""
    try:
        data = load_json(data_file)
        errors = []
        sample_count = 0
        for date_str, vals in data.items():
            dy = vals.get("dividend_yield")
            by = vals.get("bond_yield")
            prem = vals.get("premium")
            if dy is not None and by is not None and prem is not None:
                expected = round(dy - by, 4)
                # Allow tiny floating point tolerance
                if abs(prem - expected) > 0.01:
                    errors.append(f"{date_str}: expected premium {expected}, got {prem}")
                sample_count += 1
        if sample_count > 0 and len(errors) == 0:
            check3_passed = True
            check3_detail = f"Premium = Dividend Yield - Bond Yield verified for {sample_count} records."
        elif sample_count == 0:
            check3_detail = "No records with all three fields found."
        else:
            check3_detail = f"Premium calculation errors: {errors[:3]}"
    except Exception as e:
        check3_detail = f"Error verifying premium: {e}"
    checks.append({"name": "premium_calculation_correct", "passed": check3_passed, "detail": check3_detail})
    if check3_passed:
        total_score += 1

    # ── Check 4: Excel report generated ────────────────────────────────────
    excel_file = assets / "dividend_premium_report.xlsx"
    check4_passed = False
    check4_detail = ""
    try:
        if excel_file.exists() and excel_file.stat().st_size > 1000:
            import openpyxl
            wb = openpyxl.load_workbook(excel_file)
            sheet_names = wb.sheetnames
            check4_passed = "Dividend Premium" in sheet_names
            check4_detail = f"Excel file exists ({excel_file.stat().st_size} bytes). Sheets: {sheet_names}"
        elif excel_file.exists():
            check4_detail = f"Excel file exists but too small: {excel_file.stat().st_size} bytes"
        else:
            check4_detail = f"Excel file not found: {excel_file}"
    except Exception as e:
        check4_detail = f"Error reading Excel file: {e}"
    checks.append({"name": "excel_report_generated", "passed": check4_passed, "detail": check4_detail})
    if check4_passed:
        total_score += 1

    # ── Check 5: Alerts file exists and was populated ──────────────────────
    alerts_file = assets / "alerts.json"
    check5_passed = False
    check5_detail = ""
    try:
        if alerts_file.exists():
            alerts_data = load_json(alerts_file)
            alert_count = alerts_data.get("alert_count", 0)
            alerts_list = alerts_data.get("alerts", [])
            check5_passed = alert_count > 0 and len(alerts_list) > 0
            check5_detail = f"Alerts file exists. alert_count={alert_count}, alerts={len(alerts_list)}"
        else:
            check5_detail = f"Alerts file not found: {alerts_file}"
    except Exception as e:
        check5_detail = f"Error reading alerts file: {e}"
    checks.append({"name": "alerts_file_exists_and_populated", "passed": check5_passed, "detail": check5_detail})
    if check5_passed:
        total_score += 1

    # ── Check 6: Bond yield 3-consecutive-day rise alert triggered ─────────
    check6_passed = False
    check6_detail = ""
    try:
        alerts_data = load_json(alerts_file)
        alerts_list = alerts_data.get("alerts", [])
        bond_alerts = [a for a in alerts_list if a.get("type") == "bond_yield_rise"]
        check6_passed = len(bond_alerts) > 0
        if check6_passed:
            check6_detail = f"Bond yield rise alert found: {bond_alerts[0].get('message', '')[:120]}"
        else:
            check6_detail = f"No bond_yield_rise alert found. Alert types present: {[a.get('type') for a in alerts_list]}"
    except Exception as e:
        check6_detail = f"Error checking bond rise alert: {e}"
    checks.append({"name": "bond_yield_consecutive_rise_alert", "passed": check6_passed, "detail": check6_detail})
    if check6_passed:
        total_score += 1

    # ── Check 7: Premium < 1% alert triggered ─────────────────────────────
    check7_passed = False
    check7_detail = ""
    try:
        alerts_data = load_json(alerts_file)
        alerts_list = alerts_data.get("alerts", [])
        premium_alerts = [a for a in alerts_list if a.get("type") == "premium_low"]
        check7_passed = len(premium_alerts) > 0
        if check7_passed:
            pa = premium_alerts[0]
            premium_val = pa.get("premium", "N/A")
            threshold_val = pa.get("threshold", "N/A")
            # Verify the premium value is indeed < 1%
            if isinstance(premium_val, (int, float)) and premium_val < 1.0:
                check7_passed = True
                check7_detail = f"Premium < 1% alert found: premium={premium_val}%, threshold={threshold_val}%"
            else:
                check7_passed = False
                check7_detail = f"premium_low alert found but premium value {premium_val} is not < 1.0"
        else:
            check7_detail = f"No premium_low alert found. Alert types present: {[a.get('type') for a in alerts_list]}"
    except Exception as e:
        check7_detail = f"Error checking premium low alert: {e}"
    checks.append({"name": "premium_below_1pct_alert", "passed": check7_passed, "detail": check7_detail})
    if check7_passed:
        total_score += 1

    # ── Final result ───────────────────────────────────────────────────────
    all_passed = all(c["passed"] for c in checks)
    final_score = round(total_score / max_score, 4)

    result = {
        "passed": all_passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()