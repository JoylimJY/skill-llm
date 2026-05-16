import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0

    # ── Locate the output file ───────────────────────────────────────────────
    candidates = list(Path(workspace_dir).rglob("automation_plan.json"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "automation_plan.json not found anywhere in workspace"}]
        }

    plan_path = candidates[0]

    try:
        with open(plan_path, "r") as f:
            plan = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_parseable", "passed": False, "detail": f"Failed to parse JSON: {e}"}]
        }

    # ── CHECK 1: Discovery section present ───────────────────────────────────
    try:
        discovery = plan.get("discovery", {})
        has_core_value = bool(discovery.get("core_value", "").strip())
        has_bottlenecks = bool(discovery.get("bottlenecks") or discovery.get("bottleneck", ""))
        has_functions = isinstance(discovery.get("functions"), list) and len(discovery["functions"]) >= 5
        discovery_passed = has_core_value and has_bottlenecks and has_functions
        checks.append({
            "name": "discovery_section_complete",
            "passed": discovery_passed,
            "detail": f"core_value={'present' if has_core_value else 'MISSING'}, bottlenecks={'present' if has_bottlenecks else 'MISSING'}, functions_list={'≥5 items' if has_functions else 'MISSING or <5'}"
        })
        if discovery_passed:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "discovery_section_complete", "passed": False, "detail": str(e)})

    # ── CHECK 2: function_mapping present with ≥6 functions ──────────────────
    try:
        mapping = plan.get("function_mapping", [])
        has_enough = isinstance(mapping, list) and len(mapping) >= 6
        checks.append({
            "name": "function_mapping_has_6plus_entries",
            "passed": has_enough,
            "detail": f"Found {len(mapping) if isinstance(mapping, list) else 'N/A'} mapped functions (need ≥6)"
        })
        if has_enough:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "function_mapping_has_6plus_entries", "passed": False, "detail": str(e)})

    # ── CHECK 3: Approach labels must come from the SKILL.md table ───────────
    VALID_APPROACHES = {
        "Install existing skill",
        "Create custom skill",
        "Hybrid",
        "Human + agent assist",
    }
    try:
        mapping = plan.get("function_mapping", [])
        invalid_approaches = []
        valid_count = 0
        for item in mapping:
            approach = item.get("approach", "")
            # Allow case-insensitive match and minor variations
            matched = any(
                approach.lower().strip() == v.lower()
                for v in VALID_APPROACHES
            )
            if matched:
                valid_count += 1
            else:
                invalid_approaches.append(approach)
        all_valid = len(invalid_approaches) == 0 and valid_count > 0
        checks.append({
            "name": "approach_labels_from_skill_table",
            "passed": all_valid,
            "detail": f"{valid_count} valid labels. Invalid found: {invalid_approaches}"
        })
        if all_valid:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "approach_labels_from_skill_table", "passed": False, "detail": str(e)})

    # ── CHECK 4: All 4 approach types are used (coverage) ────────────────────
    try:
        mapping = plan.get("function_mapping", [])
        used_approaches = set()
        for item in mapping:
            approach = item.get("approach", "").strip()
            for v in VALID_APPROACHES:
                if approach.lower() == v.lower():
                    used_approaches.add(v)
        all_four_used = len(used_approaches) == 4
        checks.append({
            "name": "all_four_approach_types_used",
            "passed": all_four_used,
            "detail": f"Used approach types: {used_approaches} (need all 4: {VALID_APPROACHES})"
        })
        if all_four_used:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "all_four_approach_types_used", "passed": False, "detail": str(e)})

    # ── CHECK 5: Building sequence uses SKILL.md stage order ─────────────────
    STAGE_ORDER = ["internal ops", "support", "sales", "strategy"]
    try:
        sequence = plan.get("building_sequence", [])
        if not isinstance(sequence, list) or len(sequence) < 2:
            checks.append({
                "name": "building_sequence_correct_order",
                "passed": False,
                "detail": f"building_sequence must be a list of ≥2 stages. Got: {sequence}"
            })
        else:
            # Extract stage names (lowercased) from sequence items
            def get_stage_name(item):
                if isinstance(item, str):
                    return item.lower()
                elif isinstance(item, dict):
                    return (item.get("stage") or item.get("name") or item.get("phase") or "").lower()
                return ""

            stage_names = [get_stage_name(s) for s in sequence]

            # Verify that stages appear in correct relative order
            # Find indices of each known stage in stage_names
            def find_stage_index(keyword, names):
                for i, n in enumerate(names):
                    if keyword in n:
                        return i
                return None

            indices = []
            found_stages = []
            for stage_key in STAGE_ORDER:
                idx = find_stage_index(stage_key, stage_names)
                if idx is not None:
                    indices.append(idx)
                    found_stages.append(stage_key)

            # Check that found stages are in non-decreasing index order
            order_correct = indices == sorted(indices) and len(indices) >= 2
            # Also require internal ops before sales (key proprietary constraint)
            internal_before_sales = True
            idx_internal = find_stage_index("internal", stage_names)
            idx_sales = find_stage_index("sales", stage_names)
            if idx_internal is not None and idx_sales is not None:
                internal_before_sales = idx_internal < idx_sales

            passed = order_correct and internal_before_sales
            checks.append({
                "name": "building_sequence_correct_order",
                "passed": passed,
                "detail": f"Stage names found: {stage_names}. Order indices: {list(zip(found_stages, indices))}. internal_before_sales={internal_before_sales}"
            })
            if passed:
                total_score += 0.15
    except Exception as e:
        checks.append({"name": "building_sequence_correct_order", "passed": False, "detail": str(e)})

    # ── CHECK 6: Iteration protocol present per function ─────────────────────
    try:
        mapping = plan.get("function_mapping", [])
        items_with_iteration = 0
        items_with_weeks = 0
        for item in mapping:
            iteration = item.get("iteration") or item.get("iteration_protocol")
            if iteration:
                items_with_iteration += 1
                # Check for 1-2 weeks reference
                iteration_str = json.dumps(iteration).lower()
                if "week" in iteration_str:
                    items_with_weeks += 1

        iteration_coverage = items_with_iteration >= max(1, len(mapping) // 2)
        weeks_mentioned = items_with_weeks >= 1
        iteration_passed = iteration_coverage and weeks_mentioned
        checks.append({
            "name": "iteration_protocol_present",
            "passed": iteration_passed,
            "detail": f"{items_with_iteration}/{len(mapping)} functions have iteration details. {items_with_weeks} mention weeks."
        })
        if iteration_passed:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "iteration_protocol_present", "passed": False, "detail": str(e)})

    # ── CHECK 7: Red flags correctly identified ───────────────────────────────
    # Must flag: legal/compliance (agents draft, lawyers approve)
    # Must flag: trust-building/sales (agents assist, humans close)
    try:
        red_flags = plan.get("red_flags", [])
        plan_str = json.dumps(plan).lower()

        # Legal/compliance red flag
        legal_flag_keywords = ["legal", "compliance", "lawyers approve", "lawyer", "draft", "bradshaw"]
        legal_flagged = any(kw in plan_str for kw in ["agents draft", "lawyers approve", "draft.*lawyer", "lawyer.*approve"])
        # Also accept if red_flags list contains a legal item
        if isinstance(red_flags, list):
            for rf in red_flags:
                rf_str = json.dumps(rf).lower()
                if any(kw in rf_str for kw in ["legal", "compliance", "lawyer"]):
                    legal_flagged = True

        # Trust/sales red flag
        trust_flag_found = False
        trust_keywords = ["trust", "agents assist, humans close", "humans close", "relationship"]
        for kw in trust_keywords:
            if kw in plan_str:
                trust_flag_found = True

        red_flag_passed = legal_flagged and trust_flag_found
        checks.append({
            "name": "red_flags_correctly_identified",
            "passed": red_flag_passed,
            "detail": f"Legal/compliance flag found: {legal_flagged}. Trust-building/sales flag found: {trust_flag_found}."
        })
        if red_flag_passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "red_flags_correctly_identified", "passed": False, "detail": str(e)})

    # ── CHECK 8: "Human + agent assist" assigned to sales/partnerships ────────
    try:
        mapping = plan.get("function_mapping", [])
        sales_partnership_keywords = ["sales", "partner", "outreach", "referral", "corporate", "growth"]
        human_assist_for_sales = False
        for item in mapping:
            fn_name = (item.get("function") or item.get("name") or "").lower()
            approach = (item.get("approach") or "").lower()
            if any(kw in fn_name for kw in sales_partnership_keywords):
                if "human" in approach and "assist" in approach:
                    human_assist_for_sales = True

        checks.append({
            "name": "sales_mapped_to_human_agent_assist",
            "passed": human_assist_for_sales,
            "detail": f"Sales/partnership function(s) correctly mapped to 'Human + agent assist': {human_assist_for_sales}"
        })
        if human_assist_for_sales:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "sales_mapped_to_human_agent_assist", "passed": False, "detail": str(e)})

    # ── CHECK 9: "Hybrid" approach used for at least one function with company-specific rules ──
    try:
        mapping = plan.get("function_mapping", [])
        hybrid_used = False
        for item in mapping:
            approach = (item.get("approach") or "").lower()
            if "hybrid" in approach:
                hybrid_used = True
        checks.append({
            "name": "hybrid_approach_used",
            "passed": hybrid_used,
            "detail": f"At least one function mapped as 'Hybrid': {hybrid_used}"
        })
        if hybrid_used:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "hybrid_approach_used", "passed": False, "detail": str(e)})

    # ── CHECK 10: Iteration protocol has "never hand off completely on day one" concept ──
    try:
        plan_str = json.dumps(plan).lower()
        # Check for the oversight/gradual reduction concept from SKILL.md
        oversight_keywords = [
            "oversight", "hand off completely", "day one", "reduce oversight",
            "stable", "human oversight", "gradually"
        ]
        oversight_mentioned = any(kw in plan_str for kw in oversight_keywords)
        checks.append({
            "name": "iteration_oversight_concept_present",
            "passed": oversight_mentioned,
            "detail": f"Oversight/gradual handoff concept present: {oversight_mentioned}"
        })
        if oversight_mentioned:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "iteration_oversight_concept_present", "passed": False, "detail": str(e)})

    # ── Final scoring ─────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    overall_passed = passed_checks >= 7 and total_score >= 0.60

    return {
        "passed": overall_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))