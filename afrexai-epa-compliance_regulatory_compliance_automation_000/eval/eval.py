import sys
import json
import math
from pathlib import Path

def load_report(workspace):
    """Find and load compliance_assessment.json"""
    candidates = list(Path(workspace).rglob("compliance_assessment.json"))
    if not candidates:
        return None, "File compliance_assessment.json not found anywhere in workspace"
    # Use the most recently modified if multiple
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    try:
        with open(candidates[0]) as f:
            return json.load(f), str(candidates[0])
    except Exception as e:
        return None, f"Failed to parse JSON: {e}"

def run_eval(workspace):
    checks = []

    report, location_or_error = load_report(workspace)

    if report is None:
        checks.append({"name": "file_exists_and_parseable", "passed": False, "detail": location_or_error})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_exists_and_parseable", "passed": True, "detail": f"Found at: {location_or_error}"})

    # -----------------------------------------------------------------------
    # CHECK 1: RCRA Generator Classification
    # 2850 lbs/month > 2200 lbs/month => LQG (Large Quantity Generator)
    # MUST NOT say SQG or VSQG
    # -----------------------------------------------------------------------
    try:
        rcra_section = str(report).lower()
        is_lqg = "lqg" in rcra_section or "large quantity generator" in rcra_section
        is_wrong = "sqg" in rcra_section or "small quantity generator" in rcra_section or "vsqg" in rcra_section
        if is_wrong:
            checks.append({"name": "rcra_classification_lqg", "passed": False,
                           "detail": "Report incorrectly classifies as SQG or VSQG; 2850 lbs/month > 2200 lbs threshold → LQG"})
        elif is_lqg:
            checks.append({"name": "rcra_classification_lqg", "passed": True,
                           "detail": "Correctly identifies LQG status (2850 lbs/month > 2200 lbs threshold)"})
        else:
            checks.append({"name": "rcra_classification_lqg", "passed": False,
                           "detail": "No LQG classification found in report"})
    except Exception as e:
        checks.append({"name": "rcra_classification_lqg", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 2: CAA Source Classification
    # 12.3 HAP tpy > 10 tpy threshold → Major Source (Title V required)
    # Permit currently listed as minor source — this is WRONG per the skill
    # -----------------------------------------------------------------------
    try:
        report_str = str(report).lower()
        # Must flag that current minor source classification is incorrect
        has_major = "major source" in report_str or "title v" in report_str
        # Should NOT just accept the minor source classification as correct
        accepts_minor_uncritically = False
        # Check if they challenge the minor classification
        challenges_minor = ("incorrect" in report_str or "misclassified" in report_str or
                           "exceed" in report_str or "above" in report_str or
                           "major" in report_str)
        if has_major and challenges_minor:
            checks.append({"name": "caa_major_source_flag", "passed": True,
                           "detail": "Correctly identifies facility as major source (12.3 HAP tpy > 10 tpy) and flags misclassification"})
        elif has_major:
            checks.append({"name": "caa_major_source_flag", "passed": True,
                           "detail": "Major source / Title V identified (12.3 tpy HAP > 10 tpy threshold)"})
        else:
            checks.append({"name": "caa_major_source_flag", "passed": False,
                           "detail": "Failed to identify major source status; 12.3 HAP tpy exceeds 10 tpy major source threshold"})
    except Exception as e:
        checks.append({"name": "caa_major_source_flag", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 3: SPCC Plan Applicability
    # 2400 gal aboveground diesel > 1320 gal threshold → SPCC required
    # Profile says no SPCC plan on file → must flag this
    # -----------------------------------------------------------------------
    try:
        report_str = str(report).lower()
        has_spcc = "spcc" in report_str
        flags_missing = ("required" in report_str or "missing" in report_str or
                        "not on file" in report_str or "gap" in report_str or
                        "no spcc" in report_str or "absent" in report_str)
        if has_spcc and flags_missing:
            checks.append({"name": "spcc_plan_required_flagged", "passed": True,
                           "detail": "Correctly flags SPCC plan as required (2400 gal > 1320 gal threshold) and missing"})
        elif has_spcc:
            checks.append({"name": "spcc_plan_required_flagged", "passed": True,
                           "detail": "SPCC plan mentioned in report"})
        else:
            checks.append({"name": "spcc_plan_required_flagged", "passed": False,
                           "detail": "SPCC plan not addressed; 2400 gal aboveground oil exceeds 1320 gal threshold"})
    except Exception as e:
        checks.append({"name": "spcc_plan_required_flagged", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 4: Violation Risk Score — Weighted Calculation
    # Required weights: permit_currency=20%, waste_management=20%,
    # reporting_timeliness=15%, recordkeeping=15%, training=10%,
    # spill_prevention=10%, air_emissions=10%
    # Score should be in range 1.0-5.0
    # Given the severe gaps, expected score should be in HIGH (3.1-4.0) or CRITICAL (4.1-5.0) tier
    # -----------------------------------------------------------------------
    try:
        score_found = False
        risk_score = None

        def search_score(obj, depth=0):
            nonlocal score_found, risk_score
            if depth > 10:
                return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    key_lower = str(k).lower()
                    if any(term in key_lower for term in ["total", "score", "risk_score", "weighted", "overall"]):
                        if isinstance(v, (int, float)) and 1.0 <= float(v) <= 5.0:
                            risk_score = float(v)
                            score_found = True
                    search_score(v, depth+1)
            elif isinstance(obj, list):
                for item in obj:
                    search_score(item, depth+1)
            elif isinstance(obj, (int, float)):
                if 1.0 <= float(obj) <= 5.0:
                    pass  # not conclusive enough alone

        search_score(report)

        # Also look for score as string
        report_str = json.dumps(report)
        import re
        score_patterns = re.findall(r'"(?:total|risk_score|weighted_score|overall_score|score)":\s*(\d+\.?\d*)', report_str, re.IGNORECASE)
        for sp in score_patterns:
            val = float(sp)
            if 1.0 <= val <= 5.0:
                risk_score = val
                score_found = True

        if score_found and risk_score is not None:
            # Given severe gaps across all categories, expect HIGH or CRITICAL risk
            # Minimum reasonable score given the observations: most categories are 3-5
            if risk_score >= 3.0:
                checks.append({"name": "risk_score_range_and_tier", "passed": True,
                               "detail": f"Risk score {risk_score} correctly reflects HIGH or CRITICAL risk tier given facility gaps"})
            elif 2.0 <= risk_score < 3.0:
                checks.append({"name": "risk_score_range_and_tier", "passed": False,
                               "detail": f"Risk score {risk_score} seems too low; facility has critical gaps (no SPCC, expired NPDES, lapsed inspections, missed TRI) → expect 3.1+"})
            else:
                checks.append({"name": "risk_score_range_and_tier", "passed": False,
                               "detail": f"Risk score {risk_score} is implausibly low for the described violations"})
        else:
            checks.append({"name": "risk_score_range_and_tier", "passed": False,
                           "detail": "No numeric risk score (1.0-5.0 scale) found in report"})
    except Exception as e:
        checks.append({"name": "risk_score_range_and_tier", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 5: Risk Tier Labeling must use exact SKILL.md language
    # 3.1-4.0 = "High" → "immediate corrective action, consider voluntary disclosure"
    # 4.1-5.0 = "Critical" → "retain environmental counsel, self-audit before next inspection"
    # -----------------------------------------------------------------------
    try:
        report_str = str(report).lower()
        has_high = "high" in report_str
        has_critical = "critical" in report_str
        has_moderate = "moderate" in report_str
        # Must be high or critical, NOT moderate or low
        correct_tier = (has_high or has_critical) and not has_moderate
        # Also check for key mitigation language
        has_voluntary_disclosure = "voluntary disclosure" in report_str
        has_counsel = "counsel" in report_str or "corrective action" in report_str or "self-audit" in report_str

        if (has_high or has_critical) and (has_voluntary_disclosure or has_counsel):
            checks.append({"name": "risk_tier_label_and_action", "passed": True,
                           "detail": "Correct HIGH/CRITICAL tier label with appropriate action language (voluntary disclosure / corrective action / counsel)"})
        elif has_high or has_critical:
            checks.append({"name": "risk_tier_label_and_action", "passed": True,
                           "detail": "Correct HIGH or CRITICAL tier identified"})
        else:
            checks.append({"name": "risk_tier_label_and_action", "passed": False,
                           "detail": "Risk tier not labeled as HIGH or CRITICAL; given the number of gaps this is incorrect"})
    except Exception as e:
        checks.append({"name": "risk_tier_label_and_action", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 6: Reporting Calendar — Must include TRI, Tier II, and Biennial HW Report
    # with correct deadlines:
    # TRI Form R → July 1
    # Tier II → March 1
    # Biennial HW Report → March 1 (even years)
    # -----------------------------------------------------------------------
    try:
        report_str = str(report).lower()
        has_tri = "tri" in report_str or "form r" in report_str or "toxics release" in report_str
        has_tier2 = "tier ii" in report_str or "tier 2" in report_str
        has_biennial = "biennial" in report_str

        # Check specific deadlines
        has_july1 = "july 1" in report_str or "july 1st" in report_str or "07-01" in report_str or "07/01" in report_str
        has_march1 = "march 1" in report_str or "march 1st" in report_str or "03-01" in report_str or "03/01" in report_str

        reporting_score = sum([has_tri, has_tier2, has_biennial, has_july1, has_march1])

        if reporting_score >= 4:
            checks.append({"name": "reporting_calendar_completeness", "passed": True,
                           "detail": f"Reporting calendar includes TRI (July 1), Tier II, and Biennial HW with correct deadlines ({reporting_score}/5 elements)"})
        elif reporting_score >= 2:
            checks.append({"name": "reporting_calendar_completeness", "passed": False,
                           "detail": f"Reporting calendar incomplete; only {reporting_score}/5 key elements (TRI/July1, Tier II, Biennial HW/March1) found"})
        else:
            checks.append({"name": "reporting_calendar_completeness", "passed": False,
                           "detail": "Reporting calendar missing most required elements"})
    except Exception as e:
        checks.append({"name": "reporting_calendar_completeness", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 7: LQG-specific requirements cited
    # LQG requires: 90-day storage limit (not 270 — that's SQG), full contingency plan, biennial report
    # The PROPRIETARY TRAP: 90-day for LQG vs 270-day for SQG
    # -----------------------------------------------------------------------
    try:
        report_str = str(report).lower()
        has_90day = "90-day" in report_str or "90 day" in report_str or "90day" in report_str
        has_270day = "270-day" in report_str or "270 day" in report_str
        has_contingency = "contingency plan" in report_str or "contingency" in report_str
        has_biennial_hw = "biennial" in report_str

        if has_270day and not has_90day:
            checks.append({"name": "lqg_specific_requirements", "passed": False,
                           "detail": "Report cites 270-day storage limit (SQG rule) instead of 90-day (LQG rule) — critical misclassification"})
        elif has_90day and has_contingency:
            checks.append({"name": "lqg_specific_requirements", "passed": True,
                           "detail": "Correctly cites LQG 90-day storage limit and contingency plan requirement"})
        elif has_90day:
            checks.append({"name": "lqg_specific_requirements", "passed": True,
                           "detail": "90-day LQG storage limit correctly cited"})
        elif has_contingency and has_biennial_hw:
            checks.append({"name": "lqg_specific_requirements", "passed": True,
                           "detail": "LQG requirements (contingency plan, biennial report) cited"})
        else:
            checks.append({"name": "lqg_specific_requirements", "passed": False,
                           "detail": "LQG-specific requirements (90-day storage, full contingency plan, biennial report) not adequately addressed"})
    except Exception as e:
        checks.append({"name": "lqg_specific_requirements", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 8: Penalty Mitigation — must include voluntary disclosure recommendation
    # Given violation history and gaps, should recommend voluntary disclosure
    # SKILL.md: voluntary disclosure can reduce penalty 75-100%
    # -----------------------------------------------------------------------
    try:
        report_str = str(report).lower()
        has_vd = "voluntary disclosure" in report_str
        has_75_100 = ("75" in report_str and ("100" in report_str or "percent" in report_str or "%" in report_str))
        has_sep = "supplemental environmental project" in report_str or "sep" in report_str

        if has_vd and (has_75_100 or has_sep):
            checks.append({"name": "penalty_mitigation_recommendations", "passed": True,
                           "detail": "Voluntary disclosure recommended with correct penalty reduction (75-100%) and/or SEP mention"})
        elif has_vd:
            checks.append({"name": "penalty_mitigation_recommendations", "passed": True,
                           "detail": "Voluntary disclosure recommended"})
        elif has_sep:
            checks.append({"name": "penalty_mitigation_recommendations", "passed": True,
                           "detail": "SEP (Supplemental Environmental Project) mentioned for penalty mitigation"})
        else:
            checks.append({"name": "penalty_mitigation_recommendations", "passed": False,
                           "detail": "No voluntary disclosure or SEP penalty mitigation strategy found; critical omission given violation history"})
    except Exception as e:
        checks.append({"name": "penalty_mitigation_recommendations", "passed": False, "detail": f"Error: {e}"})

    # -----------------------------------------------------------------------
    # CALCULATE FINAL SCORE
    # -----------------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    # File existence check counts less
    score = passed_checks / total_checks if total_checks > 0 else 0.0

    # Overall pass requires at least 6/8 checks (75%) and the LQG classification must pass
    lqg_check = next((c for c in checks if c["name"] == "rcra_classification_lqg"), None)
    lqg_passed = lqg_check["passed"] if lqg_check else False

    overall_pass = score >= 0.75 and lqg_passed

    return {
        "passed": overall_pass,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))