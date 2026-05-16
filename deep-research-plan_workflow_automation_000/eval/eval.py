import sys
import json
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    weights = {}

    # ------------------------------------------------------------------ #
    # CHECK 1: A file exists in `plans/` directory matching the naming    #
    #          pattern `research-plan-{timestamp}.json`                   #
    # ------------------------------------------------------------------ #
    plans_dir = workspace / "plans"
    plan_files = list(plans_dir.glob("research-plan-*.json")) if plans_dir.exists() else []

    # Filter out the template and any non-timestamp named files
    timestamp_pattern = re.compile(r"research-plan-\d{10,}\.json$")
    # Also accept ISO-style timestamps like research-plan-2024-01-15T10-23-41.json
    iso_pattern = re.compile(r"research-plan-\d{4}-\d{2}-\d{2}.*\.json$")
    numeric_pattern = re.compile(r"research-plan-\d+\.json$")

    valid_plan_files = [
        f for f in plan_files
        if timestamp_pattern.match(f.name) or iso_pattern.match(f.name) or numeric_pattern.match(f.name)
    ]

    check1_passed = len(valid_plan_files) >= 1
    checks.append({
        "name": "plan_file_in_correct_location",
        "passed": check1_passed,
        "detail": f"Found {len(valid_plan_files)} valid plan file(s) in plans/ with timestamp naming. Files: {[f.name for f in valid_plan_files]}"
    })
    weights["plan_file_in_correct_location"] = 0.15

    # Load the plan for subsequent checks
    plan_data = None
    parse_error = None
    if valid_plan_files:
        # Use the most recently created/modified plan
        target_file = sorted(valid_plan_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
        try:
            with open(target_file) as f:
                plan_data = json.load(f)
        except Exception as e:
            parse_error = str(e)

    # ------------------------------------------------------------------ #
    # CHECK 2: JSON is valid and parseable                                 #
    # ------------------------------------------------------------------ #
    check2_passed = plan_data is not None
    checks.append({
        "name": "plan_json_valid",
        "passed": check2_passed,
        "detail": f"JSON parsing {'succeeded' if check2_passed else f'failed: {parse_error}'}"
    })
    weights["plan_json_valid"] = 0.10

    # ------------------------------------------------------------------ #
    # CHECK 3: Required field `topic` present and non-empty string        #
    # ------------------------------------------------------------------ #
    if plan_data:
        topic_ok = (
            "topic" in plan_data and
            isinstance(plan_data["topic"], str) and
            len(plan_data["topic"].strip()) > 5
        )
    else:
        topic_ok = False
    checks.append({
        "name": "required_field_topic",
        "passed": topic_ok,
        "detail": f"topic = {repr(plan_data.get('topic', 'MISSING')) if plan_data else 'N/A'}"
    })
    weights["required_field_topic"] = 0.08

    # ------------------------------------------------------------------ #
    # CHECK 4: Required field `research_questions` — non-empty array      #
    # ------------------------------------------------------------------ #
    if plan_data:
        rq = plan_data.get("research_questions", None)
        rq_ok = (
            rq is not None and
            isinstance(rq, list) and
            len(rq) >= 2 and
            all(isinstance(q, str) and len(q.strip()) > 5 for q in rq)
        )
        rq_detail = f"research_questions has {len(rq) if isinstance(rq, list) else 'N/A (not a list)'} items"
    else:
        rq_ok = False
        rq_detail = "No plan data"
    checks.append({
        "name": "required_field_research_questions",
        "passed": rq_ok,
        "detail": rq_detail
    })
    weights["required_field_research_questions"] = 0.12

    # ------------------------------------------------------------------ #
    # CHECK 5: Required field `report_requirements` present with          #
    #          sub-fields: sections (list), depth (str), min_sources (int)#
    # ------------------------------------------------------------------ #
    if plan_data:
        rr = plan_data.get("report_requirements", None)
        rr_is_dict = isinstance(rr, dict)
        has_sections = rr_is_dict and isinstance(rr.get("sections"), list) and len(rr.get("sections", [])) >= 1
        has_depth = rr_is_dict and isinstance(rr.get("depth"), str) and len(rr.get("depth", "")) > 0
        has_min_sources = rr_is_dict and isinstance(rr.get("min_sources"), int) and rr.get("min_sources", 0) >= 1
        rr_ok = rr_is_dict and has_sections and has_depth and has_min_sources
        rr_detail = (
            f"report_requirements: dict={rr_is_dict}, "
            f"sections={'OK' if has_sections else 'MISSING/INVALID'}, "
            f"depth={'OK' if has_depth else 'MISSING'}, "
            f"min_sources={'OK' if has_min_sources else 'MISSING/INVALID'}"
        )
    else:
        rr_ok = False
        rr_detail = "No plan data"
    checks.append({
        "name": "required_field_report_requirements",
        "passed": rr_ok,
        "detail": rr_detail
    })
    weights["required_field_report_requirements"] = 0.15

    # ------------------------------------------------------------------ #
    # CHECK 6: Topic is relevant to CRISPR / gene editing / rare diseases #
    # ------------------------------------------------------------------ #
    if plan_data and plan_data.get("topic"):
        topic_text = plan_data["topic"].lower()
        relevant_keywords = ["crispr", "gene edit", "gene therapy", "rare disease", "genetic", "therapeutic"]
        topic_relevant = any(kw in topic_text for kw in relevant_keywords)
    else:
        topic_relevant = False
    checks.append({
        "name": "topic_domain_relevance",
        "passed": topic_relevant,
        "detail": f"Topic relevance to CRISPR/gene editing domain: {'yes' if topic_relevant else 'no'}. Topic: {repr(plan_data.get('topic','')) if plan_data else 'N/A'}"
    })
    weights["topic_domain_relevance"] = 0.10

    # ------------------------------------------------------------------ #
    # CHECK 7: Plan does NOT contain HOW-to-search fields                 #
    #          (keywords, search_engines, search_terms, search_strategy)  #
    # ------------------------------------------------------------------ #
    if plan_data:
        forbidden_keys = {"keywords", "search_engines", "search_terms", "search_strategy",
                          "search_queries", "sources_to_use", "databases"}
        found_forbidden = forbidden_keys.intersection(set(plan_data.keys()))
        no_how_fields = len(found_forbidden) == 0
        how_detail = f"Forbidden how-to-search keys found: {found_forbidden}" if found_forbidden else "No forbidden how-to-search fields found"
    else:
        no_how_fields = False
        how_detail = "No plan data"
    checks.append({
        "name": "plan_no_how_to_search_fields",
        "passed": no_how_fields,
        "detail": how_detail
    })
    weights["plan_no_how_to_search_fields"] = 0.10

    # ------------------------------------------------------------------ #
    # CHECK 8: Optional `scope` field — if present, must have             #
    #          include/exclude structure                                   #
    # ------------------------------------------------------------------ #
    if plan_data:
        scope = plan_data.get("scope", None)
        if scope is None:
            # Optional field, absence is acceptable but lower score
            scope_ok = True
            scope_detail = "scope field absent (optional, acceptable)"
            scope_weight_bonus = False
        elif isinstance(scope, dict):
            has_include = "include" in scope and isinstance(scope["include"], list)
            has_exclude = "exclude" in scope and isinstance(scope["exclude"], list)
            scope_ok = has_include or has_exclude
            scope_detail = f"scope present: include={'OK' if has_include else 'MISSING'}, exclude={'OK' if has_exclude else 'MISSING'}"
            scope_weight_bonus = scope_ok
        else:
            scope_ok = False
            scope_detail = f"scope is present but not a dict: {type(scope)}"
            scope_weight_bonus = False
    else:
        scope_ok = False
        scope_detail = "No plan data"
        scope_weight_bonus = False
    checks.append({
        "name": "optional_scope_structure",
        "passed": scope_ok,
        "detail": scope_detail
    })
    weights["optional_scope_structure"] = 0.05

    # ------------------------------------------------------------------ #
    # CHECK 9: min_sources >= 8 (default from skill spec)                 #
    # ------------------------------------------------------------------ #
    if plan_data and isinstance(plan_data.get("report_requirements"), dict):
        ms = plan_data["report_requirements"].get("min_sources", 0)
        min_sources_ok = isinstance(ms, int) and ms >= 8
        ms_detail = f"min_sources = {ms} ({'OK' if min_sources_ok else 'should be >= 8'})"
    else:
        min_sources_ok = False
        ms_detail = "No report_requirements or no min_sources"
    checks.append({
        "name": "min_sources_at_least_8",
        "passed": min_sources_ok,
        "detail": ms_detail
    })
    weights["min_sources_at_least_8"] = 0.08

    # ------------------------------------------------------------------ #
    # CHECK 10: `sections` array includes required report sections        #
    #           Must include at least 3 of: executive_summary, findings,  #
    #           conclusion, references                                     #
    # ------------------------------------------------------------------ #
    if plan_data and isinstance(plan_data.get("report_requirements"), dict):
        sections = plan_data["report_requirements"].get("sections", [])
        required_sections = {"executive_summary", "findings", "conclusion", "references"}
        # Normalize: lowercase, replace spaces with underscores
        normalized_sections = {s.lower().replace(" ", "_") for s in sections if isinstance(s, str)}
        matched = required_sections.intersection(normalized_sections)
        sections_ok = len(matched) >= 3
        sections_detail = f"sections present: {sorted(normalized_sections)}, matched standard: {sorted(matched)}"
    else:
        sections_ok = False
        sections_detail = "No report_requirements or no sections"
    checks.append({
        "name": "sections_include_standard_fields",
        "passed": sections_ok,
        "detail": sections_detail
    })
    weights["sections_include_standard_fields"] = 0.07

    # ------------------------------------------------------------------ #
    # COMPUTE FINAL SCORE                                                  #
    # ------------------------------------------------------------------ #
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)

    # Overall pass: must pass checks 1,2,3,4,5 (the core structural requirements)
    core_checks = {"plan_file_in_correct_location", "plan_json_valid",
                   "required_field_topic", "required_field_research_questions",
                   "required_field_report_requirements"}
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)
    passed = core_passed and score >= 0.70

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    try:
        result = evaluate(sys.argv[1])
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": f"Evaluator crashed: {str(e)}"}]
        }

    print(json.dumps(result, indent=2))