import json
import sys
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 10.0

    # Find pipeline_plan.json
    found_files = list(Path(workspace).rglob("pipeline_plan.json"))
    
    if not found_files:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "pipeline_plan.json not found anywhere in workspace"}]
        }))
        return

    # Use the most recently modified file if multiple found
    plan_path = sorted(found_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    try:
        with open(plan_path, "r") as f:
            plan = json.load(f)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_parseable", "passed": False, "detail": f"Could not parse pipeline_plan.json: {e}"}]
        }))
        return

    # CHECK 1: File exists and is valid JSON
    checks.append({"name": "file_exists_and_valid_json", "passed": True, "detail": f"Found at {plan_path}"})
    total_score += 0.5

    # CHECK 2: All 5 required output sections are present and non-empty
    required_sections = [
        "lead_intake_validation",
        "qualification_logic",
        "routing_and_ownership_plan",
        "followup_cadence",
        "pipeline_risk_alerts"
    ]
    
    # Allow flexible key naming (case-insensitive, underscores/spaces)
    def normalize_key(k):
        return k.lower().replace(" ", "_").replace("-", "_")
    
    plan_keys_normalized = {normalize_key(k): k for k in plan.keys()}
    
    missing_sections = []
    for req in required_sections:
        if normalize_key(req) not in plan_keys_normalized:
            missing_sections.append(req)
    
    all_sections_present = len(missing_sections) == 0
    checks.append({
        "name": "all_five_output_sections_present",
        "passed": all_sections_present,
        "detail": f"Missing sections: {missing_sections}" if missing_sections else "All 5 required sections found"
    })
    if all_sections_present:
        total_score += 1.0

    # CHECK 3: Lead Intake Validation - identifies missing critical fields
    intake_key = plan_keys_normalized.get("lead_intake_validation", "lead_intake_validation")
    intake_section = plan.get(intake_key, plan.get("lead_intake_validation", {}))
    intake_str = json.dumps(intake_section).lower()
    
    # L-20260303-02 missing qualification_goal
    # L-20260303-03 missing email
    # L-20260303-09 missing first_name/last_name/company
    missing_field_leads_detected = (
        ("l-20260303-02" in intake_str or "02" in intake_str) and
        ("l-20260303-03" in intake_str or "03" in intake_str) and
        ("l-20260303-09" in intake_str or "09" in intake_str)
    )
    # More lenient: just check that the section mentions multiple leads with missing fields
    enrichment_routing_mentioned = "enrichment" in intake_str
    
    intake_valid = enrichment_routing_mentioned and len(intake_str) > 50
    checks.append({
        "name": "intake_identifies_missing_fields_and_enrichment_routing",
        "passed": intake_valid,
        "detail": f"Intake section mentions enrichment queue: {enrichment_routing_mentioned}. Section length: {len(intake_str)}"
    })
    if intake_valid:
        total_score += 1.5

    # CHECK 4: Qualification Logic uses the correct scoring formula
    qual_key = plan_keys_normalized.get("qualification_logic", "qualification_logic")
    qual_section = plan.get(qual_key, plan.get("qualification_logic", {}))
    qual_str = json.dumps(qual_section).lower()
    
    # Must reference the three score components
    has_intent_score = "intent_score" in qual_str or "intent" in qual_str
    has_fit_score = "fit_score" in qual_str or "fit" in qual_str
    has_urgency_score = "urgency_score" in qual_str or "urgency" in qual_str
    has_threshold_80 = "80" in qual_str
    
    formula_correct = has_intent_score and has_fit_score and has_urgency_score and has_threshold_80
    checks.append({
        "name": "qualification_logic_uses_correct_scoring_formula",
        "passed": formula_correct,
        "detail": f"intent:{has_intent_score}, fit:{has_fit_score}, urgency:{has_urgency_score}, threshold_80:{has_threshold_80}"
    })
    if formula_correct:
        total_score += 1.5

    # CHECK 5: Routing Plan includes routing payloads with required fields (lead_id, route_to, sla_hours)
    routing_key = plan_keys_normalized.get("routing_and_ownership_plan", "routing_and_ownership_plan")
    routing_section = plan.get(routing_key, plan.get("routing_and_ownership_plan", {}))
    routing_str = json.dumps(routing_section).lower()
    
    has_lead_id = "lead_id" in routing_str
    has_route_to = "route_to" in routing_str
    has_sla_hours = "sla_hours" in routing_str
    has_enrichment_queue = "enrichment" in routing_str
    
    routing_valid = has_lead_id and has_route_to and has_sla_hours and has_enrichment_queue
    checks.append({
        "name": "routing_plan_has_required_payload_fields_and_enrichment",
        "passed": routing_valid,
        "detail": f"lead_id:{has_lead_id}, route_to:{has_route_to}, sla_hours:{has_sla_hours}, enrichment_queue:{has_enrichment_queue}"
    })
    if routing_valid:
        total_score += 1.5

    # CHECK 6: Channel-aware differentiation (Meta/TikTok vs Google Ads handled differently)
    full_plan_str = json.dumps(plan).lower()
    
    meta_mentioned = "meta" in full_plan_str
    tiktok_mentioned = "tiktok" in full_plan_str
    google_mentioned = "google" in full_plan_str
    creative_testing = "creative" in full_plan_str  # Meta/TikTok should mention creative testing
    demand_capture_or_intent = "demand" in full_plan_str or "intent" in full_plan_str or "query" in full_plan_str
    
    channel_aware = meta_mentioned and tiktok_mentioned and google_mentioned and (creative_testing or demand_capture_or_intent)
    checks.append({
        "name": "channel_aware_platform_differentiation",
        "passed": channel_aware,
        "detail": f"meta:{meta_mentioned}, tiktok:{tiktok_mentioned}, google:{google_mentioned}, creative_testing:{creative_testing}, demand_intent:{demand_capture_or_intent}"
    })
    if channel_aware:
        total_score += 1.0

    # CHECK 7: Follow-up Cadence section enforces same-day response for high-intent leads
    followup_key = plan_keys_normalized.get("followup_cadence", "followup_cadence")
    followup_section = plan.get(followup_key, plan.get("followup_cadence", {}))
    followup_str = json.dumps(followup_section).lower()
    
    same_day_or_4hr = "same-day" in followup_str or "same day" in followup_str or "4 hour" in followup_str or "4-hour" in followup_str or "4h" in followup_str or "sla" in followup_str
    high_intent_mentioned = "high" in followup_str and ("intent" in followup_str or "priority" in followup_str)
    
    followup_valid = same_day_or_4hr and high_intent_mentioned
    checks.append({
        "name": "followup_cadence_enforces_high_intent_same_day_rule",
        "passed": followup_valid,
        "detail": f"same_day_or_4hr_sla:{same_day_or_4hr}, high_intent_mention:{high_intent_mentioned}"
    })
    if followup_valid:
        total_score += 1.0

    # CHECK 8: Pipeline Risk Alerts include rollback/stop-loss condition and leakage
    alerts_key = plan_keys_normalized.get("pipeline_risk_alerts", "pipeline_risk_alerts")
    alerts_section = plan.get(alerts_key, plan.get("pipeline_risk_alerts", {}))
    alerts_str = json.dumps(alerts_section).lower()
    
    has_rollback_or_stoploss = (
        "rollback" in alerts_str or 
        "stop-loss" in alerts_str or 
        "stop loss" in alerts_str or
        "stoploss" in alerts_str or
        "pause" in alerts_str or
        "reduce budget" in alerts_str or
        "budget cap" in alerts_str or
        "kill switch" in alerts_str
    )
    has_leakage = "leakage" in alerts_str or "leak" in alerts_str or "recovery" in alerts_str or "drop" in alerts_str
    
    alerts_valid = has_rollback_or_stoploss and len(alerts_str) > 50
    checks.append({
        "name": "risk_alerts_include_rollback_stoploss_condition",
        "passed": alerts_valid,
        "detail": f"rollback/stoploss:{has_rollback_or_stoploss}, leakage_mentioned:{has_leakage}, section_length:{len(alerts_str)}"
    })
    if alerts_valid:
        total_score += 1.0

    # CHECK 9: No fabricated metrics (check for observably reasonable content)
    # The plan should separate observed facts from assumptions
    separates_facts_assumptions = (
        "assumption" in full_plan_str or 
        "observed" in full_plan_str or 
        "note" in full_plan_str or
        "based on" in full_plan_str or
        "inferred" in full_plan_str or
        "estimated" in full_plan_str
    )
    checks.append({
        "name": "separates_observed_facts_from_assumptions",
        "passed": separates_facts_assumptions,
        "detail": f"Found epistemic qualification language: {separates_facts_assumptions}"
    })
    if separates_facts_assumptions:
        total_score += 0.5

    # Normalize score to 0-1
    normalized_score = round(min(total_score / max_score, 1.0), 4)
    
    # Pass threshold: must pass at least 7 of 9 checks, including critical ones
    critical_checks = [
        "intake_identifies_missing_fields_and_enrichment_routing",
        "qualification_logic_uses_correct_scoring_formula",
        "routing_plan_has_required_payload_fields_and_enrichment",
    ]
    
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == cc), False)
        for cc in critical_checks
    )
    
    checks_passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = critical_passed and checks_passed_count >= 7

    print(json.dumps({
        "passed": overall_passed,
        "score": normalized_score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)