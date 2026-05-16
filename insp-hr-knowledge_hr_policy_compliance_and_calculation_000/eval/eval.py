import sys
import json
import os
from pathlib import Path

def load_report(workspace):
    """Find the compliance_report.json file anywhere in the workspace."""
    matches = list(Path(workspace).rglob("compliance_report.json"))
    if not matches:
        return None, "File compliance_report.json not found anywhere in workspace."
    return matches[0], None

def run_checks(workspace):
    checks = []
    score = 0.0
    total_weight = 0.0

    report_path, err = load_report(workspace)
    if report_path is None:
        checks.append({"name": "file_exists", "passed": False, "detail": err})
        return checks, 0.0

    checks.append({"name": "file_exists", "passed": True, "detail": str(report_path)})

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "file_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return checks, 0.0

    checks.append({"name": "file_parseable", "passed": True, "detail": "Valid JSON."})

    # -----------------------------------------------------------------------
    # CHECK 1: Resignation notice period compliance
    # Li Wei is a CONFIRMED (转正) employee -> must give 1 month notice.
    # Resignation email sent: 2026-03-10, desired last day: 2026-03-20 (only 10 days).
    # This is NON-COMPLIANT. The correct earliest last day would be ~2026-04-10.
    # Weight: 15%
    # -----------------------------------------------------------------------
    weight = 15.0
    total_weight += weight
    try:
        section = report.get("resignation_compliance", report.get("resignation", {}))
        # Must flag as non-compliant
        compliant = section.get("notice_period_compliant", None)
        required_days = section.get("required_notice_days", section.get("notice_days_required", None))
        actual_days = section.get("actual_notice_days", section.get("days_given", None))

        passed = False
        detail = ""

        # Check compliance flag
        if isinstance(compliant, bool) and compliant == False:
            passed = True
            detail = "Correctly flagged non-compliant."
        elif isinstance(compliant, str) and compliant.lower() in ("false", "no", "non-compliant", "不合规", "违规"):
            passed = True
            detail = "Correctly flagged non-compliant (string)."
        else:
            detail = f"Expected non-compliant but got: compliant={compliant}"

        # Also check required days = 30 (1 month = ~30 days)
        if required_days is not None:
            try:
                rd = int(required_days)
                if rd == 30 or rd == 31:
                    detail += f" Required notice days correctly identified as {rd}."
                else:
                    detail += f" Warning: required_notice_days={rd}, expected ~30."
            except:
                pass

        checks.append({"name": "resignation_notice_non_compliant", "passed": passed, "detail": detail})
        if passed:
            score += weight
    except Exception as e:
        checks.append({"name": "resignation_notice_non_compliant", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 2: Required offboarding tables identified
    # Li Wei has loans (借款) and rebates (返点), so all 3 tables are required:
    # Table 1: Project Handover (always required)
    # Table 2: Loans (has_outstanding_loan=True)
    # Table 3: Rebate details (has_rebates_to_collect=True, AND is a media buyer 媒介)
    # Weight: 10%
    # -----------------------------------------------------------------------
    weight = 10.0
    total_weight += weight
    try:
        tables = report.get("required_tables", report.get("offboarding_tables", []))
        if isinstance(tables, list):
            table_nums = set()
            for t in tables:
                if isinstance(t, (int, float)):
                    table_nums.add(int(t))
                elif isinstance(t, str):
                    for n in ["1","2","3"]:
                        if n in t:
                            table_nums.add(int(n))
                elif isinstance(t, dict):
                    for v in t.values():
                        for n in ["1","2","3"]:
                            if n in str(v):
                                table_nums.add(int(n))
            passed = {1,2,3}.issubset(table_nums)
            detail = f"Tables identified: {sorted(table_nums)}. Expected {{1,2,3}}."
        else:
            passed = False
            detail = f"required_tables is not a list: {tables}"
        checks.append({"name": "all_three_tables_required", "passed": passed, "detail": detail})
        if passed:
            score += weight
    except Exception as e:
        checks.append({"name": "all_three_tables_required", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 3: Weekday OT compensatory leave calculation
    # Rules: OT starts 30 min after end (18:30), so OT starts at 19:00. Min 1 hour. 1:1 ratio. Floor to whole hours.
    #
    # 2026-03-02: check_out 21:30. OT = 21:30 - 19:00 = 2.5h -> floor = 2h comp
    # 2026-03-03: check_out 19:45. OT = 19:45 - 19:00 = 45min < 1h -> 0h comp
    # 2026-03-04: check_out 22:15. OT = 22:15 - 19:00 = 3.25h -> floor = 3h comp
    # 2026-03-09: check_out 19:00. OT = 19:00 - 19:00 = 0 -> 0h comp
    # 2026-03-10: check_out 20:30. OT = 20:30 - 19:00 = 1.5h -> floor = 1h comp
    # 2026-03-16: check_out 23:00. OT = 23:00 - 19:00 = 4h -> 4h comp
    # Total weekday OT comp: 2 + 0 + 3 + 0 + 1 + 4 = 10h
    # Weight: 20%
    # -----------------------------------------------------------------------
    weight = 20.0
    total_weight += weight
    EXPECTED_WEEKDAY_OT_HOURS = 10
    try:
        ot_section = report.get("overtime", report.get("overtime_summary", {}))
        weekday_ot = ot_section.get("weekday_compensatory_hours",
                      ot_section.get("weekday_ot_hours",
                      ot_section.get("weekday_comp_hours", None)))
        if weekday_ot is None:
            # Try top level
            weekday_ot = report.get("weekday_compensatory_hours",
                          report.get("weekday_ot_hours", None))
        
        passed = False
        detail = f"Expected {EXPECTED_WEEKDAY_OT_HOURS}h, got: {weekday_ot}"
        if weekday_ot is not None:
            try:
                if abs(float(weekday_ot) - EXPECTED_WEEKDAY_OT_HOURS) < 0.01:
                    passed = True
                    detail = f"Correct: {weekday_ot}h weekday compensatory leave."
            except:
                pass
        checks.append({"name": "weekday_ot_comp_hours_correct", "passed": passed, "detail": detail})
        if passed:
            score += weight
    except Exception as e:
        checks.append({"name": "weekday_ot_comp_hours_correct", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 4: Weekend OT compensatory leave calculation
    # Rules: Min 2 continuous hours to count. 1:0.7 ratio. MUST have waijin punch.
    #
    # 2026-03-07: 1.5h, waijin=True -> < 2h -> 0h comp
    # 2026-03-08: 4.5h, waijin=True -> 4.5 * 0.7 = 3.15h -> floor = 3h comp
    # 2026-03-14: 3h, waijin=False -> no waijin punch -> 0h comp (can't be counted)
    # Total weekend OT comp: 3h
    # Weight: 20%
    # -----------------------------------------------------------------------
    weight = 20.0
    total_weight += weight
    EXPECTED_WEEKEND_OT_HOURS = 3
    try:
        ot_section = report.get("overtime", report.get("overtime_summary", {}))
        weekend_ot = ot_section.get("weekend_compensatory_hours",
                      ot_section.get("weekend_ot_hours",
                      ot_section.get("weekend_comp_hours", None)))
        if weekend_ot is None:
            weekend_ot = report.get("weekend_compensatory_hours",
                          report.get("weekend_ot_hours", None))

        passed = False
        detail = f"Expected {EXPECTED_WEEKEND_OT_HOURS}h, got: {weekend_ot}"
        if weekend_ot is not None:
            try:
                if abs(float(weekend_ot) - EXPECTED_WEEKEND_OT_HOURS) < 0.01:
                    passed = True
                    detail = f"Correct: {weekend_ot}h weekend compensatory leave."
            except:
                pass
        checks.append({"name": "weekend_ot_comp_hours_correct", "passed": passed, "detail": detail})
        if passed:
            score += weight
    except Exception as e:
        checks.append({"name": "weekend_ot_comp_hours_correct", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 5: Expense claim violations
    # EXP001: 招待费, 4 persons, 920 RMB. Max is 200/person -> 4*200=800. 920 > 800 -> VIOLATION
    # EXP002: 团建费, 8 persons, 800 RMB. 100/person -> 8*100=800 -> COMPLIANT (exactly at limit)
    # EXP003: 团建费, 5 persons, 400 RMB. 100*5=500, so 400 is fine amount-wise.
    #         BUT: After resignation email (2026-03-10), team-building expenses must be
    #         submitted by the direct leader (不可由离职员工自己申请).
    #         So EXP003 should be flagged as invalid/non-compliant submitter.
    # EXP004: 误餐费, 50 RMB -> compliant (standard execution)
    # EXP005: NBC, no invoice -> VIOLATION (all reimbursements require invoice)
    # Submission date 2026-03-26 > 24th -> DELAYED to next cycle (not rejected, just delayed)
    #
    # We check: EXP001 flagged, EXP003 flagged, EXP005 flagged
    # Weight: 20%
    # -----------------------------------------------------------------------
    weight = 20.0
    total_weight += weight
    try:
        exp_section = report.get("expense_violations", report.get("expense_compliance", report.get("expenses", {})))
        
        violations = []
        if isinstance(exp_section, list):
            violations = [str(v) for v in exp_section]
        elif isinstance(exp_section, dict):
            violations_raw = exp_section.get("violations", exp_section.get("flagged_claims", []))
            if isinstance(violations_raw, list):
                violations = [str(v) for v in violations_raw]
            # also try keys at top level
            for key in ["EXP001", "EXP003", "EXP005"]:
                entry = exp_section.get(key, {})
                if isinstance(entry, dict):
                    compliant_val = entry.get("compliant", entry.get("valid", True))
                    if compliant_val == False or str(compliant_val).lower() in ("false","no","violation","违规","invalid"):
                        violations.append(key)

        # Convert to string for searching
        violations_str = json.dumps(exp_section).upper()

        exp001_flagged = "EXP001" in violations_str
        exp003_flagged = "EXP003" in violations_str
        exp005_flagged = "EXP005" in violations_str
        submission_late = any(kw in json.dumps(exp_section).lower() for kw in 
                              ["delay", "late", "next", "下月", "顺延", "26", "deadline"])

        # Also search at top level report
        full_str = json.dumps(report).upper()
        if not exp001_flagged:
            # Check for patterns indicating EXP001 flagged anywhere
            exp001_flagged = ("EXP001" in full_str and 
                              any(w in full_str for w in ["EXCEED","OVER","VIOLAT","超","违"]))
        if not exp003_flagged:
            exp003_flagged = ("EXP003" in full_str and 
                              any(w in full_str for w in ["LEADER","DIRECT","INVALID","RESIGN","离职","不可","须由"]))
        if not exp005_flagged:
            exp005_flagged = ("EXP005" in full_str and 
                              any(w in full_str for w in ["INVOICE","NO INVOICE","发票","缺","未提供"]))

        passed = exp001_flagged and exp003_flagged and exp005_flagged
        detail = (f"EXP001(招待费超额) flagged={exp001_flagged}, "
                  f"EXP003(离职后团建提交人) flagged={exp003_flagged}, "
                  f"EXP005(无发票) flagged={exp005_flagged}. "
                  f"Submission late noted={submission_late}")
        checks.append({"name": "expense_violations_identified", "passed": passed, "detail": detail})
        if passed:
            score += weight
    except Exception as e:
        checks.append({"name": "expense_violations_identified", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 6: Late deductions calculation
    # 2026-03-02: check_in 09:45 -> 15 min late -> 0 < T <= 15 -> 50 RMB
    # 2026-03-04: check_in 10:05 -> 5 min late -> 0 < T <= 15 -> 50 RMB
    # 2026-03-09: check_in 10:20 -> 20 min late -> 15 < T <= 30 -> 100 RMB
    # 2026-03-11: missed punch (check_in=None) -> counts as 1 补卡 use, no deduction if within 5/month
    # Total deductions: 50 + 50 + 100 = 200 RMB
    # Weight: 15%
    # -----------------------------------------------------------------------
    weight = 15.0
    total_weight += weight
    EXPECTED_LATE_DEDUCTION = 200
    try:
        attend_section = report.get("attendance_deductions", report.get("attendance", report.get("deductions", {})))
        late_deduction = attend_section.get("late_deduction_rmb",
                          attend_section.get("total_late_fine",
                          attend_section.get("total_deduction_rmb", None)))
        if late_deduction is None:
            late_deduction = report.get("late_deduction_rmb",
                              report.get("total_late_fine", None))

        passed = False
        detail = f"Expected {EXPECTED_LATE_DEDUCTION} RMB, got: {late_deduction}"
        if late_deduction is not None:
            try:
                if abs(float(late_deduction) - EXPECTED_LATE_DEDUCTION) < 0.01:
                    passed = True
                    detail = f"Correct: {late_deduction} RMB total late deductions."
            except:
                pass
        checks.append({"name": "late_deduction_correct", "passed": passed, "detail": detail})
        if passed:
            score += weight
    except Exception as e:
        checks.append({"name": "late_deduction_correct", "passed": False, "detail": f"Error: {e}"})

    # Normalize score to 0-1
    final_score = score / 100.0 if total_weight > 0 else 0.0

    return checks, final_score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, score = run_checks(workspace)
    passed = score >= 0.6
    print(json.dumps({
        "passed": passed,
        "score": round(score, 4),
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()