import sys
import json
import math
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # ── Load ground-truth data ─────────────────────────────────────────────
    try:
        with open(workspace / "data/raw/jan_cohort_counts.json") as f:
            cohort_gt = json.load(f)
        jan_active = cohort_gt["active_per_month"]
        jan_initial = cohort_gt["initial_size"]  # 120
    except Exception as e:
        add_check("ground_truth_load", False, f"Could not load cohort ground truth: {e}")
        jan_active = None
        jan_initial = 120

    # Expected cohort retention percentages (rounded to nearest integer for tolerance)
    # month 0 = 120/120 = 100%, month 1 = jan_active[1]/120, etc.
    # Month 1 = index 1, Month 3 = index 3, Month 6 = index 6, Month 12 = index 11
    expected_cohort = {}
    if jan_active:
        expected_cohort = {
            "month_1":  round(jan_active[1] / jan_initial * 100, 1),
            "month_3":  round(jan_active[3] / jan_initial * 100, 1),
            "month_6":  round(jan_active[6] / jan_initial * 100, 1),
            "month_12": round(jan_active[11] / jan_initial * 100, 1),
        }

    # Feb & Mar churn rates
    feb_churn_expected = round(18 / 200 * 100, 2)   # 9.0%
    mar_churn_expected = round(11 / 210 * 100, 2)   # ~5.24%
    feb_retention_expected = round(100 - feb_churn_expected, 2)
    mar_retention_expected = round(100 - mar_churn_expected, 2)

    # Top churn reason: "Not using it enough" (35 out of 100)
    top_churn_reason_expected = "Not using it enough"

    # Benchmark classification:
    # Feb churn = 9% → "Needs work" (5-10% range)
    # Mar churn ≈ 5.24% → borderline "Needs work" (>5%)
    feb_benchmark_expected = "Needs work"

    # 12-month cohort retention: if > 70% → "Healthy", 50-70% → "Needs work", <50% → "Critical"
    if jan_active:
        m12_pct = jan_active[11] / jan_initial * 100
        if m12_pct > 70:
            cohort_12m_benchmark = "Healthy"
        elif m12_pct >= 50:
            cohort_12m_benchmark = "Needs work"
        else:
            cohort_12m_benchmark = "Critical"
    else:
        cohort_12m_benchmark = None

    # ── Find the output report ──────────────────────────────────────────────
    report_files = list(workspace.rglob("retention_analysis_report.json"))
    if not report_files:
        add_check("report_file_exists", False, "Could not find retention_analysis_report.json anywhere in workspace")
        return finalize(checks)
    
    report_path = report_files[0]
    add_check("report_file_exists", True, f"Found report at {report_path}")

    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        add_check("report_parseable", False, f"JSON parse error: {e}")
        return finalize(checks)
    add_check("report_parseable", True, "Report is valid JSON")

    # ── CHECK 1: Monthly churn rates ──────────────────────────────────────
    try:
        metrics = report.get("monthly_metrics", report.get("metrics", report.get("churn_metrics", {})))
        
        # Try to find Feb churn rate
        feb_data = None
        if isinstance(metrics, dict):
            for key in ["2024-02", "february", "feb", "Feb"]:
                if key in metrics:
                    feb_data = metrics[key]
                    break
            if feb_data is None and "months" in metrics:
                for m in metrics["months"]:
                    if "02" in str(m.get("month","")) or "feb" in str(m.get("month","")).lower():
                        feb_data = m
                        break
        elif isinstance(metrics, list):
            for m in metrics:
                if "02" in str(m.get("month","")) or "feb" in str(m.get("month","")).lower():
                    feb_data = m
                    break
        
        if feb_data is None:
            # Try flat structure
            feb_data = report
        
        # Extract churn rate value (accept various key names)
        churn_val = None
        for key in ["churn_rate", "monthly_churn_rate", "churn", "churn_rate_pct", "churn_rate_percent"]:
            if key in (feb_data or {}):
                churn_val = feb_data[key]
                break
        
        if churn_val is None:
            # Try to find any numeric value close to 9.0
            add_check("feb_churn_rate", False, f"Could not find February churn rate. Expected ~{feb_churn_expected}%. feb_data={str(feb_data)[:200]}")
        else:
            val = float(str(churn_val).replace("%",""))
            tolerance = 0.5
            ok = abs(val - feb_churn_expected) <= tolerance
            add_check("feb_churn_rate", ok, 
                f"Feb churn rate: got {val}, expected {feb_churn_expected}% (±{tolerance}). Formula: customers_lost/customers_at_start × 100")
    except Exception as e:
        add_check("feb_churn_rate", False, f"Error checking Feb churn rate: {e}")

    # ── CHECK 2: March churn rate ─────────────────────────────────────────
    try:
        mar_data = None
        if isinstance(metrics, dict):
            for key in ["2024-03", "march", "mar", "Mar"]:
                if key in metrics:
                    mar_data = metrics[key]
                    break
            if mar_data is None and "months" in metrics:
                for m in metrics.get("months",[]):
                    if "03" in str(m.get("month","")) or "mar" in str(m.get("month","")).lower():
                        mar_data = m
                        break
        elif isinstance(metrics, list):
            for m in metrics:
                if "03" in str(m.get("month","")) or "mar" in str(m.get("month","")).lower():
                    mar_data = m
                    break

        if mar_data is None:
            mar_data = report

        churn_val = None
        for key in ["churn_rate", "monthly_churn_rate", "churn", "churn_rate_pct", "churn_rate_percent"]:
            if key in (mar_data or {}):
                churn_val = mar_data[key]
                break

        if churn_val is None:
            add_check("mar_churn_rate", False, f"Could not find March churn rate. Expected ~{mar_churn_expected}%")
        else:
            val = float(str(churn_val).replace("%",""))
            tolerance = 0.5
            ok = abs(val - mar_churn_expected) <= tolerance
            add_check("mar_churn_rate", ok,
                f"Mar churn rate: got {val}, expected {mar_churn_expected}% (±{tolerance})")
    except Exception as e:
        add_check("mar_churn_rate", False, f"Error checking Mar churn rate: {e}")

    # ── CHECK 3: Benchmark classification ─────────────────────────────────
    try:
        report_str = json.dumps(report).lower()
        has_needs_work = "needs work" in report_str or "needs_work" in report_str
        add_check("benchmark_classification", has_needs_work,
            f"Expected 'Needs work' benchmark for Feb 9% churn (5-10% range per SKILL.md). Found in report: {has_needs_work}")
    except Exception as e:
        add_check("benchmark_classification", False, f"Error: {e}")

    # ── CHECK 4: Cohort retention percentages ─────────────────────────────
    try:
        cohort_section = None
        for key in ["cohort_retention", "cohort", "jan_cohort", "retention_cohort", "cohort_analysis"]:
            if key in report:
                cohort_section = report[key]
                break
        
        if cohort_section is None:
            # Search entire report for month_1, month_3 etc.
            cohort_section = report

        # Check month_1 retention
        m1_val = None
        for key in ["month_1", "month1", "1_month", "m1", "month_1_retention", "1month"]:
            if key in (cohort_section or {}):
                m1_val = cohort_section[key]
                break

        m12_val = None
        for key in ["month_12", "month12", "12_month", "m12", "month_12_retention", "12month"]:
            if key in (cohort_section or {}):
                m12_val = cohort_section[key]
                break
        
        cohort_checks_passed = 0
        cohort_detail = []
        
        if m1_val is not None and expected_cohort:
            v = float(str(m1_val).replace("%",""))
            ok = abs(v - expected_cohort["month_1"]) <= 3.0
            cohort_checks_passed += (1 if ok else 0)
            cohort_detail.append(f"M1: got {v}, expected {expected_cohort['month_1']}%")
        else:
            cohort_detail.append(f"M1 not found in cohort section")

        if m12_val is not None and expected_cohort:
            v = float(str(m12_val).replace("%",""))
            ok = abs(v - expected_cohort["month_12"]) <= 3.0
            cohort_checks_passed += (1 if ok else 0)
            cohort_detail.append(f"M12: got {v}, expected {expected_cohort['month_12']}%")
        else:
            cohort_detail.append(f"M12 not found in cohort section")

        add_check("cohort_retention_values", cohort_checks_passed >= 1,
            f"Cohort retention checks: {'; '.join(cohort_detail)}")
    except Exception as e:
        add_check("cohort_retention_values", False, f"Error checking cohort: {e}")

    # ── CHECK 5: 12-month cohort benchmark ───────────────────────────────
    try:
        report_str_lower = json.dumps(report).lower()
        if cohort_12m_benchmark:
            benchmark_lower = cohort_12m_benchmark.lower().replace(" ", "")
            # Check for the benchmark text
            found = (cohort_12m_benchmark.lower() in report_str_lower or 
                     benchmark_lower in report_str_lower.replace(" ","").replace("_",""))
            add_check("cohort_12m_benchmark", found,
                f"Expected cohort 12-month benchmark '{cohort_12m_benchmark}' in report. "
                f"12-month retention = {expected_cohort.get('month_12','?')}%")
    except Exception as e:
        add_check("cohort_12m_benchmark", False, f"Error: {e}")

    # ── CHECK 6: Top churn reason identified ─────────────────────────────
    try:
        churn_reasons_section = None
        for key in ["churn_reasons", "cancellation_reasons", "top_churn_reasons", "churn_analysis", "why_customers_churn"]:
            if key in report:
                churn_reasons_section = report[key]
                break
        
        report_str = json.dumps(report).lower()
        top_reason_found = ("not using it enough" in report_str or 
                           "not using" in report_str and "enough" in report_str)
        
        # Also check it's identified as TOP/primary reason
        is_top = False
        if churn_reasons_section:
            s = json.dumps(churn_reasons_section).lower()
            if "not using it enough" in s or ("not using" in s and "enough" in s):
                # Check for rank/top indicators
                if any(word in s for word in ["top", "primary", "1", "first", "#1", "main", "number one", "most common"]):
                    is_top = True
                # Also accept if it has highest count/percentage
                if "35" in s or "0.35" in s:
                    is_top = True
        
        if top_reason_found and not is_top:
            # Accept if it's just present in a list with highest value
            is_top = top_reason_found  # Partial credit
        
        add_check("top_churn_reason_identified", top_reason_found,
            f"Expected 'Not using it enough' as top churn reason (35/100 responses). Found: {top_reason_found}")
    except Exception as e:
        add_check("top_churn_reason_identified", False, f"Error: {e}")

    # ── CHECK 7: Churn reason distribution has all 5 canonical categories ─
    try:
        report_str = json.dumps(report).lower()
        canonical = [
            "not using it enough",
            "too expensive",
            "missing a feature",
            "found a better alternative",
            "didn't deliver expected value",
        ]
        found_count = sum(1 for c in canonical if any(word in report_str for word in c.split()[:3]))
        all_found = found_count >= 4
        add_check("canonical_churn_categories", all_found,
            f"Found {found_count}/5 canonical SKILL.md churn reason categories in report")
    except Exception as e:
        add_check("canonical_churn_categories", False, f"Error: {e}")

    # ── CHECK 8: Re-engagement email sequence (5 emails, 14-day cadence) ──
    try:
        reeng_section = None
        for key in ["reengagement_campaign", "re_engagement_campaign", "reengagement", "re_engagement", 
                    "win_back_campaign", "winback", "email_sequence", "reengagement_email_sequence"]:
            if key in report:
                reeng_section = report[key]
                break
        
        if reeng_section is None:
            add_check("reengagement_5_emails", False, "No re-engagement section found in report")
        else:
            emails = None
            for key in ["emails", "sequence", "campaign_emails", "steps"]:
                if key in reeng_section:
                    emails = reeng_section[key]
                    break
            if emails is None and isinstance(reeng_section, list):
                emails = reeng_section
            
            if emails and isinstance(emails, list):
                email_count = len(emails)
                add_check("reengagement_5_emails", email_count == 5,
                    f"Expected exactly 5 emails in re-engagement sequence, got {email_count}")
            else:
                add_check("reengagement_5_emails", False, 
                    f"Could not find email list in re-engagement section. Keys: {list(reeng_section.keys()) if isinstance(reeng_section, dict) else type(reeng_section)}")
    except Exception as e:
        add_check("reengagement_5_emails", False, f"Error: {e}")

    # ── CHECK 9: Re-engagement day offsets (0, 3, 7, 10, 14) ─────────────
    try:
        required_days = {0, 3, 7, 10, 14}
        found_days = set()
        
        if reeng_section:
            reeng_str = json.dumps(reeng_section)
            # Look for day values
            import re
            day_patterns = re.findall(r'"day[_\s]?(?:offset|number|num)?"\s*:\s*(\d+)', reeng_str, re.IGNORECASE)
            day_patterns += re.findall(r'"send_day"\s*:\s*(\d+)', reeng_str, re.IGNORECASE)
            day_patterns += re.findall(r'"day"\s*:\s*(\d+)', reeng_str, re.IGNORECASE)
            for d in day_patterns:
                found_days.add(int(d))
        
        correct_days = found_days == required_days or required_days.issubset(found_days)
        add_check("reengagement_day_offsets", correct_days,
            f"Expected days {{0,3,7,10,14}}, found days {found_days}. "
            f"SKILL.md specifies 5 emails at Day 0, 3, 7, 10, 14 over 14-day window.")
    except Exception as e:
        add_check("reengagement_day_offsets", False, f"Error: {e}")

    # ── CHECK 10: Re-engagement last email purpose (last call / cancellation mention) ──
    try:
        if reeng_section:
            reeng_str = json.dumps(reeng_section).lower()
            has_last_call = any(phrase in reeng_str for phrase in [
                "last call", "last chance", "cancellation", "cancel", "don't want to see you go",
                "don't want to lose you", "pause", "discount"
            ])
            add_check("reengagement_day14_purpose", has_last_call,
                "Day 14 email should reference cancellation risk, pause option, or discount (SKILL.md Email 5 pattern)")
        else:
            add_check("reengagement_day14_purpose", False, "No re-engagement section to check")
    except Exception as e:
        add_check("reengagement_day14_purpose", False, f"Error: {e}")

    # ── CHECK 11: At-risk trigger criteria applied (30 days + 50% drop) ───
    try:
        report_str = json.dumps(report).lower()
        has_30_day_trigger = "30" in report_str and ("day" in report_str or "days" in report_str)
        has_50_pct_trigger = "50" in report_str and ("%" in report_str or "percent" in report_str or "drop" in report_str)
        has_at_risk_section = any(k in report for k in ["at_risk_users", "at_risk", "risk_triggers", "risk_identification"])
        
        trigger_check = (has_30_day_trigger or has_50_pct_trigger) and has_at_risk_section
        add_check("at_risk_trigger_criteria", trigger_check,
            f"Expected at-risk trigger criteria (30 days inactive OR 50% usage drop). "
            f"30-day ref: {has_30_day_trigger}, 50% ref: {has_50_pct_trigger}, at-risk section: {has_at_risk_section}")
    except Exception as e:
        add_check("at_risk_trigger_criteria", False, f"Error: {e}")

    return finalize(checks)


def finalize(checks):
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    passed = passed_count >= int(total * 0.7)  # 70% threshold
    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(ws)
    print(json.dumps(result, indent=2))