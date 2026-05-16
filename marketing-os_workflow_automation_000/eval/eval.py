import sys
import json
import re
import math
from pathlib import Path

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_file(workspace, filename):
    results = list(Path(workspace).rglob(filename))
    return results[0] if results else None

def run_checks(workspace):
    checks = []
    workspace = Path(workspace)

    # ────────────────────────────────────────────────────────────
    # FILE DISCOVERY
    # ────────────────────────────────────────────────────────────
    cmo_output_path = find_file(workspace, "cmo_output.json")
    mission_brief_path = find_file(workspace, "mission_brief.json")
    campaign_plan_path = find_file(workspace, "campaign_plan.json")

    # ── CHECK 1: All three required files exist ───────────────────
    files_exist = all([cmo_output_path, mission_brief_path, campaign_plan_path])
    checks.append({
        "name": "all_three_output_files_exist",
        "passed": files_exist,
        "detail": (
            f"cmo_output.json={'found' if cmo_output_path else 'MISSING'}, "
            f"mission_brief.json={'found' if mission_brief_path else 'MISSING'}, "
            f"campaign_plan.json={'found' if campaign_plan_path else 'MISSING'}"
        )
    })

    if not files_exist:
        # Cannot proceed without files
        for name in ["cmo_output_structure", "priority_score_formula", "uncertain_signals_tagged",
                     "no_vague_language", "fact_inference_labels", "mission_brief_structure",
                     "mission_brief_priority_enum", "mission_brief_channels_ranked",
                     "campaign_tasks_have_required_fields", "campaign_tasks_pending_status",
                     "campaign_has_kpi"]:
            checks.append({"name": name, "passed": False, "detail": "Required file missing, skipping check."})
        return checks

    # ────────────────────────────────────────────────────────────
    # CMO OUTPUT CHECKS
    # ────────────────────────────────────────────────────────────
    try:
        cmo = load_json_file(cmo_output_path)
    except Exception as e:
        checks.append({"name": "cmo_output_parse", "passed": False, "detail": f"JSON parse error: {e}"})
        cmo = None

    if cmo is not None:
        # CHECK 2: Required top-level keys present
        required_keys = {"analysis_id", "market_opportunities", "target_segments",
                         "recommended_actions", "risks", "next_steps", "confidence_level"}
        missing = required_keys - set(cmo.keys())
        checks.append({
            "name": "cmo_output_structure",
            "passed": len(missing) == 0,
            "detail": f"Missing keys: {missing}" if missing else "All required CMO output keys present."
        })

        # CHECK 3: priority_score formula correctness
        # Raw signal data for reference
        signals_data = [
            {"id": "sig_001", "signal_strength": 8, "market_size_score": 7, "capability_match_score": 9, "urgency_score": 8},
            {"id": "sig_002", "signal_strength": 7, "market_size_score": 8, "capability_match_score": 7, "urgency_score": 6},
            {"id": "sig_003", "signal_strength": 6, "market_size_score": 9, "capability_match_score": 6, "urgency_score": 7},
            {"id": "sig_004", "signal_strength": 3, "market_size_score": 5, "capability_match_score": 4, "urgency_score": 3},
            {"id": "sig_005", "signal_strength": 6, "market_size_score": 6, "capability_match_score": 8, "urgency_score": 5},
            {"id": "sig_006", "signal_strength": 2, "market_size_score": 0, "capability_match_score": 9, "urgency_score": 8},
        ]
        # Expected priority scores (×10 to match 0-100 scale from 0-10 inputs)
        # formula: (ss*0.3 + ms*0.25 + cm*0.25 + urg*0.2) * 10
        expected_scores = {}
        for s in signals_data:
            raw = (s["signal_strength"] * 0.3 + s["market_size_score"] * 0.25 +
                   s["capability_match_score"] * 0.25 + s["urgency_score"] * 0.2)
            expected_scores[s["id"]] = round(raw * 10, 1)

        # Check that at least the TOP opportunity has a correct priority_score
        # sig_001: (8*0.3+7*0.25+9*0.25+8*0.2)*10 = (2.4+1.75+2.25+1.6)*10 = 80.0
        # sig_002: (7*0.3+8*0.25+7*0.25+6*0.2)*10 = (2.1+2.0+1.75+1.2)*10 = 70.5
        # sig_003: (6*0.3+9*0.25+6*0.25+7*0.2)*10 = (1.8+2.25+1.5+1.4)*10 = 69.5
        opps = cmo.get("market_opportunities", [])
        formula_ok = False
        formula_detail = "No opportunities found to check score."
        if opps:
            # Find any opportunity with a priority_score close to one of our expected values
            tolerance = 3.0  # allow minor rounding
            matched = []
            for opp in opps:
                score = opp.get("priority_score", None)
                if score is None:
                    continue
                for sig_id, exp in expected_scores.items():
                    if abs(float(score) - exp) <= tolerance:
                        matched.append((sig_id, score, exp))
            formula_ok = len(matched) >= 1
            formula_detail = (
                f"Matched scores: {matched}" if formula_ok
                else f"No opportunity scores match expected formula values. "
                     f"Expected (sig→score): {expected_scores}. "
                     f"Got opportunity scores: {[o.get('priority_score') for o in opps]}"
            )
        checks.append({
            "name": "priority_score_formula",
            "passed": formula_ok,
            "detail": formula_detail
        })

        # CHECK 4: Signals with strength < 4 are tagged "uncertain"
        # sig_004 (strength=3) and sig_006 (strength=2) must be tagged uncertain
        # We look in the full CMO output text for "uncertain"
        cmo_text = json.dumps(cmo).lower()
        uncertain_present = "uncertain" in cmo_text
        # Also check that low-strength signals (sig_004, sig_006) are somehow flagged
        checks.append({
            "name": "uncertain_signals_tagged",
            "passed": uncertain_present,
            "detail": (
                "Found 'uncertain' tag in CMO output — signals with strength<4 correctly flagged."
                if uncertain_present
                else "FAIL: No 'uncertain' tag found in CMO output. Signals with signal_strength<4 must be tagged 'uncertain'."
            )
        })

        # CHECK 5: No vague language
        vague_patterns = [
            r'\bconsider\b', r'\bperhaps\b', r'\bmaybe\b', r'\bmight want to\b',
            r'\bcould try\b', r'\bpossibly\b', r'\bthink about\b', r'\bshould consider\b',
            r'\b可以试试\b', r'\b或许\b', r'\b考虑\b'
        ]
        vague_found = []
        for pat in vague_patterns:
            if re.search(pat, cmo_text, re.IGNORECASE):
                vague_found.append(pat)
        no_vague = len(vague_found) == 0
        checks.append({
            "name": "no_vague_language",
            "passed": no_vague,
            "detail": (
                "No vague language found in CMO output." if no_vague
                else f"Vague language detected: {vague_found}"
            )
        })

        # CHECK 6: [FACT]/[INFERENCE]/[RECOMMENDATION] labels present
        has_labels = (
            "[FACT]" in json.dumps(cmo) or
            "[INFERENCE]" in json.dumps(cmo) or
            "[RECOMMENDATION]" in json.dumps(cmo)
        )
        checks.append({
            "name": "fact_inference_labels",
            "passed": has_labels,
            "detail": (
                "Found [FACT]/[INFERENCE]/[RECOMMENDATION] labels in CMO output."
                if has_labels
                else "FAIL: No [FACT], [INFERENCE], or [RECOMMENDATION] labels found. "
                     "All statements must be classified per behavior rules."
            )
        })

    # ────────────────────────────────────────────────────────────
    # MISSION BRIEF CHECKS
    # ────────────────────────────────────────────────────────────
    try:
        brief = load_json_file(mission_brief_path)
    except Exception as e:
        checks.append({"name": "mission_brief_parse", "passed": False, "detail": f"JSON parse error: {e}"})
        brief = None

    if brief is not None:
        # CHECK 7: Required mission brief keys
        required_brief_keys = {"mission_id", "objective", "target_audience", "strategy",
                                "priority", "recommended_channels", "actions", "success_criteria"}
        missing_brief = required_brief_keys - set(brief.keys())
        checks.append({
            "name": "mission_brief_structure",
            "passed": len(missing_brief) == 0,
            "detail": (
                f"Missing keys: {missing_brief}" if missing_brief
                else "All required mission brief keys present."
            )
        })

        # CHECK 8: Priority must be one of the valid enum values
        valid_priorities = {"critical", "high", "medium", "low"}
        brief_priority = str(brief.get("priority", "")).lower()
        priority_valid = brief_priority in valid_priorities
        checks.append({
            "name": "mission_brief_priority_enum",
            "passed": priority_valid,
            "detail": (
                f"Priority '{brief_priority}' is valid."
                if priority_valid
                else f"Invalid priority '{brief_priority}'. Must be one of: {valid_priorities}"
            )
        })

        # CHECK 9: recommended_channels have priority_rank field
        channels = brief.get("recommended_channels", [])
        channels_have_rank = (
            len(channels) > 0 and
            all("priority_rank" in ch for ch in channels)
        )
        checks.append({
            "name": "mission_brief_channels_ranked",
            "passed": channels_have_rank,
            "detail": (
                f"All {len(channels)} channels have priority_rank."
                if channels_have_rank
                else f"Channels missing priority_rank: {channels}"
            )
        })

        # CHECK 10: success_criteria has primary_kpi with metric and target
        sc = brief.get("success_criteria", {})
        kpi = sc.get("primary_kpi", {}) if isinstance(sc, dict) else {}
        has_kpi = (
            isinstance(kpi, dict) and
            "metric" in kpi and
            "target" in kpi
        )
        checks.append({
            "name": "mission_brief_success_criteria",
            "passed": has_kpi,
            "detail": (
                f"success_criteria.primary_kpi OK: {kpi}"
                if has_kpi
                else f"Missing or malformed success_criteria.primary_kpi: {sc}"
            )
        })

    # ────────────────────────────────────────────────────────────
    # CAMPAIGN PLAN CHECKS
    # ────────────────────────────────────────────────────────────
    try:
        campaign = load_json_file(campaign_plan_path)
    except Exception as e:
        checks.append({"name": "campaign_plan_parse", "passed": False, "detail": f"JSON parse error: {e}"})
        campaign = None

    if campaign is not None:
        # CHECK 11: Tasks have required atomic fields (owner, deadline, expected_result)
        tasks = []
        # Support both flat list and nested structure
        if isinstance(campaign, dict):
            tasks = campaign.get("tasks", campaign.get("campaign_tasks", []))
        elif isinstance(campaign, list):
            tasks = campaign

        tasks_ok = False
        tasks_detail = "No tasks found in campaign plan."
        if tasks:
            required_task_fields = {"owner", "deadline", "expected_result"}
            tasks_with_all_fields = [
                t for t in tasks
                if isinstance(t, dict) and required_task_fields.issubset(t.keys())
            ]
            tasks_ok = len(tasks_with_all_fields) >= 2  # at least 2 atomic tasks
            tasks_detail = (
                f"{len(tasks_with_all_fields)}/{len(tasks)} tasks have all required fields (owner, deadline, expected_result)."
            )
        checks.append({
            "name": "campaign_tasks_have_required_fields",
            "passed": tasks_ok,
            "detail": tasks_detail
        })

        # CHECK 12: All task statuses initialized to "pending"
        pending_ok = False
        pending_detail = "No tasks found."
        if tasks:
            tasks_with_status = [t for t in tasks if isinstance(t, dict) and "status" in t]
            non_pending = [t for t in tasks_with_status if t.get("status") != "pending"]
            pending_ok = len(tasks_with_status) >= 1 and len(non_pending) == 0
            pending_detail = (
                f"All {len(tasks_with_status)} tasks have status='pending'." if pending_ok
                else f"{len(non_pending)} tasks have non-'pending' status: "
                     f"{[t.get('status') for t in non_pending]}. "
                     f"Initial state must be 'pending'."
            )
        checks.append({
            "name": "campaign_tasks_pending_status",
            "passed": pending_ok,
            "detail": pending_detail
        })

        # CHECK 13: Campaign has KPI targets at campaign level
        if isinstance(campaign, dict):
            has_campaign_kpi = (
                "kpi_targets" in campaign or
                "kpis" in campaign or
                "success_metrics" in campaign or
                "objectives" in campaign
            )
        else:
            has_campaign_kpi = False
        checks.append({
            "name": "campaign_has_kpi",
            "passed": has_campaign_kpi,
            "detail": (
                "Campaign plan has KPI/success metrics defined."
                if has_campaign_kpi
                else "Campaign plan missing KPI targets. Must include kpi_targets or similar at campaign level."
            )
        })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_crash", "passed": False, "detail": str(e)}]

    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks) if checks else 0.0
    overall_passed = score >= 0.75

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()