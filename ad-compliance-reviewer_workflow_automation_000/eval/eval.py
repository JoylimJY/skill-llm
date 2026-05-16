import sys
import json
import re
from pathlib import Path

def load_report(workspace):
    matches = list(Path(workspace).rglob("compliance_review_report.json"))
    if not matches:
        return None, "File 'compliance_review_report.json' not found anywhere in workspace."
    if len(matches) > 1:
        # Accept any one, prefer the most recently placed
        matches.sort(key=lambda p: str(p))
    return matches[0], None

def run_eval(workspace):
    checks = []

    # --- Load the report ---
    report_path, err = load_report(workspace)
    if err:
        checks.append({"name": "file_exists", "passed": False, "detail": err})
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append({"name": "file_exists", "passed": True, "detail": str(report_path)})

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            raw = f.read()
        report = json.loads(raw)
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        score = round(1/10, 3)
        return {"passed": False, "score": score, "checks": checks}

    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON."})

    report_str = raw.lower()

    # ---- CHECK 1: All 5 required output sections present ----
    required_sections = [
        ("intent_summary", ["intent_summary", "intent summary"]),
        ("findings", ["findings"]),
        ("action_plan", ["action_plan", "action plan"]),
        ("risks_and_guardrails", ["risks_and_guardrails", "risks and guardrails", "risks", "guardrails"]),
        ("handoff_payload", ["handoff_payload", "handoff payload"]),
    ]
    sections_found = 0
    section_details = []
    for section_name, variants in required_sections:
        found = any(v in report_str for v in variants)
        sections_found += int(found)
        section_details.append(f"{section_name}: {'FOUND' if found else 'MISSING'}")

    all_sections_present = sections_found == 5
    checks.append({
        "name": "all_5_output_sections_present",
        "passed": all_sections_present,
        "detail": "; ".join(section_details)
    })

    # ---- CHECK 2: Intent Summary includes inferred KPI marked as assumption ----
    # The brief has empty kpi_targets. Per Decision Rules: "If KPI is missing, infer likely primary KPI
    # from goal and mark assumption explicitly."
    has_inferred_kpi = False
    assumption_markers = ["assumption", "inferred", "assumed", "mark as assumption", "assumed kpi", "inferred kpi"]
    kpi_terms = ["cpa", "roas", "cpl", "revenue", "sales", "conversion", "cost per acquisition"]
    
    has_assumption_marker = any(m in report_str for m in assumption_markers)
    has_kpi_term = any(k in report_str for k in kpi_terms)
    has_inferred_kpi = has_assumption_marker and has_kpi_term

    checks.append({
        "name": "inferred_kpi_marked_as_assumption",
        "passed": has_inferred_kpi,
        "detail": (
            f"Assumption marker found: {has_assumption_marker}; "
            f"KPI term found: {has_kpi_term}. "
            "Decision Rule requires inferred KPIs to be explicitly marked as assumptions."
        )
    })

    # ---- CHECK 3: Explicit platform naming (Meta, Google Ads, TikTok Ads — NOT 'Facebook', 'AdWords') ----
    # SKILL.md: "Keep naming explicit: Meta, Google Ads, TikTok Ads..."
    correct_names = ["meta", "google ads", "tiktok ads"]
    banned_names_found = []
    # Check for banned loose names used WITHOUT correct counterpart nearby
    # We'll check that correct names appear (lenient: at least 2 of 3)
    correct_found = [n for n in correct_names if n in report_str]
    # Also check that at least 'google ads' and 'meta' appear (most critical renamings)
    critical_correct = ["meta", "google ads"]
    critical_found = [n for n in critical_correct if n in report_str]

    platform_naming_ok = len(correct_found) >= 2 and len(critical_found) == 2
    checks.append({
        "name": "explicit_platform_naming",
        "passed": platform_naming_ok,
        "detail": (
            f"Correct platform names found: {correct_found}. "
            f"Required at least: {critical_correct}. "
            "SKILL.md mandates explicit platform names: Meta, Google Ads, TikTok Ads."
        )
    })

    # ---- CHECK 4: Compliance violations detected — specific violations must be flagged ----
    # The ad copies contain: 'guaranteed cure', 'FDA Approved' (false claim), 'doctors hate',
    # '70% off' urgency, 'clinically proven to eliminate illness', '300% immunity boost',
    # targeting cancer treatment searchers, 'lose 30 lbs in 30 days'
    critical_violations = [
        ("guaranteed_cure_claim", ["guaranteed", "cure", "guarantee"]),
        ("fda_approved_false_claim", ["fda approved", "fda-approved", "fda approval"]),
        ("doctors_hate_pattern", ["doctors hate", "doctors don't want", "doctor"]),
        ("unsubstantiated_health_claim", ["clinically proven", "300%", "scientifically guaranteed", "unsubstantiated"]),
        ("weight_loss_claim", ["30 lbs", "30 pounds", "melt fat", "lose weight", "weight loss claim"]),
    ]
    violations_found = 0
    violation_details = []
    for vname, vterms in critical_violations:
        found = any(t in report_str for t in vterms)
        violations_found += int(found)
        violation_details.append(f"{vname}: {'DETECTED' if found else 'MISSED'}")

    # Must catch at least 4 out of 5 violation categories
    violations_ok = violations_found >= 4
    checks.append({
        "name": "critical_violations_detected",
        "passed": violations_ok,
        "detail": f"Violations detected: {violations_found}/5. {'; '.join(violation_details)}"
    })

    # ---- CHECK 5: Compliant rewrites provided ----
    # SKILL.md: "Detect compliance risks and provide concrete compliant rewrites before publishing."
    # Must have actual rewritten ad copy or rewrite suggestions
    rewrite_indicators = [
        "rewrite", "compliant version", "revised", "suggested copy", "alternative", 
        "compliant alternative", "replace with", "instead use", "corrected"
    ]
    has_rewrite = any(r in report_str for r in rewrite_indicators)
    checks.append({
        "name": "compliant_rewrites_provided",
        "passed": has_rewrite,
        "detail": (
            f"Rewrite indicators found: {[r for r in rewrite_indicators if r in report_str]}. "
            "SKILL.md requires concrete compliant rewrites."
        )
    })

    # ---- CHECK 6: High compliance risk triggers pre-launch gate ----
    # SKILL.md: "If compliance risk is detected, route to Ads Compliance Review before launch."
    # And Decision Rules: "If policy or account risk appears high, require compliance or account checks before scale."
    # Must recommend holding/blocking launch pending compliance resolution.
    launch_gate_indicators = [
        "before launch", "prior to launch", "do not launch", "hold launch", "pause launch",
        "compliance check before", "compliance review before", "block", "halt", "stop launch",
        "require compliance", "compliance gate", "pre-launch"
    ]
    has_launch_gate = any(g in report_str for g in launch_gate_indicators)
    checks.append({
        "name": "high_risk_pre_launch_gate",
        "passed": has_launch_gate,
        "detail": (
            f"Launch gate indicators found: {[g for g in launch_gate_indicators if g in report_str]}. "
            "SKILL.md Decision Rules: high policy risk must require compliance checks before scale."
        )
    })

    # ---- CHECK 7: Sensitive audience targeting risk flagged ----
    # The brief mentions "targeting people who searched for cancer treatments" — must be flagged
    sensitive_audience_terms = [
        "cancer", "sensitive audience", "health condition targeting", "medical targeting",
        "prohibited targeting", "sensitive category", "health interest targeting"
    ]
    has_audience_flag = any(t in report_str for t in sensitive_audience_terms)
    checks.append({
        "name": "sensitive_audience_targeting_flagged",
        "passed": has_audience_flag,
        "detail": (
            f"Sensitive audience indicators found: {[t for t in sensitive_audience_terms if t in report_str]}. "
            "Brief explicitly mentions targeting cancer treatment searchers — must be flagged."
        )
    })

    # ---- CHECK 8: Handoff Payload has structured fields ----
    # Must be a structured object (not just a string mention)
    handoff_check = False
    handoff_detail = "Handoff payload section not found or not structured."
    try:
        # Look for handoff_payload as a key in the JSON
        def find_handoff(obj, depth=0):
            if depth > 10:
                return None
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if "handoff" in k.lower():
                        return v
                    result = find_handoff(v, depth+1)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_handoff(item, depth+1)
                    if result is not None:
                        return result
            return None

        handoff_val = find_handoff(report)
        if handoff_val is not None and isinstance(handoff_val, dict) and len(handoff_val) >= 2:
            handoff_check = True
            handoff_detail = f"Handoff payload found with {len(handoff_val)} fields: {list(handoff_val.keys())[:5]}"
        elif handoff_val is not None:
            handoff_detail = f"Handoff payload found but has only {len(handoff_val) if isinstance(handoff_val, dict) else 'non-dict'} content."
        else:
            handoff_detail = "No 'handoff' key found in JSON structure."
    except Exception as e:
        handoff_detail = f"Error checking handoff payload: {e}"

    checks.append({
        "name": "handoff_payload_structured",
        "passed": handoff_check,
        "detail": handoff_detail
    })

    # ---- CHECK 9: No fabricated data / facts separated from assumptions ----
    # SKILL.md: "Do not fabricate data, performance outcomes, or policy approvals."
    # "Separate facts from assumptions in every recommendation."
    # Check that assumptions are called out (already partially covered in check 2),
    # and that no fake performance numbers are asserted as real
    # We check that the word "assumption" or "fact" appears (signals discipline)
    separation_indicators = ["assumption", "assumed", "fact:", "note:", "inferred", "no historical data"]
    has_separation = any(s in report_str for s in separation_indicators)
    checks.append({
        "name": "facts_separated_from_assumptions",
        "passed": has_separation,
        "detail": (
            f"Separation indicators found: {[s for s in separation_indicators if s in report_str]}. "
            "SKILL.md requires explicit separation of facts and assumptions."
        )
    })

    # ---- CHECK 10: At least 3 trigger keywords from When To Trigger present ----
    # SKILL.md Quality Checklist: "At least 3 registry keywords appear in When To Trigger"
    trigger_keywords = [
        "ads", "advertising", "campaign", "growth", "strategy",
        "revenue", "profit", "roi", "roas", "cpa",
        "budget", "bidding", "traffic", "conversion", "funnel",
        "meta", "googleads", "tiktokads", "youtubeads", "amazonads", "shopifyads", "dsp"
    ]
    # Normalize: collapse spaces for compound keywords
    report_str_nospace = report_str.replace(" ", "").replace("_", "").replace("-", "")
    found_keywords = [k for k in trigger_keywords if k.replace(" ","") in report_str_nospace]
    has_3_keywords = len(found_keywords) >= 3
    checks.append({
        "name": "at_least_3_trigger_keywords",
        "passed": has_3_keywords,
        "detail": (
            f"Found {len(found_keywords)} trigger keywords: {found_keywords[:10]}. "
            "Quality Checklist requires at least 3 registry keywords from When To Trigger."
        )
    })

    # --- Scoring ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    # Weight critical checks more heavily
    critical_check_names = {
        "file_exists": 1,
        "valid_json": 1,
        "all_5_output_sections_present": 2,
        "critical_violations_detected": 2,
        "compliant_rewrites_provided": 2,
        "high_risk_pre_launch_gate": 1,
        "inferred_kpi_marked_as_assumption": 1,
        "explicit_platform_naming": 1,
    }
    weighted_score = 0
    max_weighted = 0
    for c in checks:
        w = critical_check_names.get(c["name"], 1)
        max_weighted += w
        if c["passed"]:
            weighted_score += w

    score = round(weighted_score / max_weighted, 3) if max_weighted > 0 else 0.0

    # Must pass file_exists, valid_json, all_5_sections, critical_violations, and compliant_rewrites to overall pass
    must_pass = ["file_exists", "valid_json", "all_5_output_sections_present",
                 "critical_violations_detected", "compliant_rewrites_provided"]
    all_must_pass = all(
        any(c["name"] == mp and c["passed"] for c in checks)
        for mp in must_pass
    )

    overall_passed = all_must_pass and score >= 0.65

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))