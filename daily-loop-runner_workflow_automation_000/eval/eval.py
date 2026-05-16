import sys
import json
import os
from pathlib import Path

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def run_eval(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 10.0

    # ── Find output file ─────────────────────────────────────────────────────
    output_path = None
    for candidate in Path(workspace).rglob("daily_loop_output.json"):
        output_path = candidate
        break

    if output_path is None:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "daily_loop_output.json not found anywhere in workspace"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "output_file_exists", "passed": True,
                    "detail": f"Found at {output_path}"})
    total_score += 0.5

    # ── Parse output ─────────────────────────────────────────────────────────
    try:
        output = load_json(output_path)
    except Exception as e:
        checks.append({"name": "output_parseable", "passed": False,
                        "detail": f"JSON parse error: {e}"})
        print(json.dumps({"passed": False, "score": 0.5, "checks": checks}))
        return

    checks.append({"name": "output_parseable", "passed": True, "detail": "Valid JSON"})
    total_score += 0.5

    # ── Expect a list of two run results ─────────────────────────────────────
    if not isinstance(output, list) or len(output) < 2:
        checks.append({"name": "output_is_two_run_array", "passed": False,
                        "detail": f"Expected a JSON array with 2 run results, got: {type(output).__name__} length={len(output) if isinstance(output, list) else 'N/A'}"})
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    checks.append({"name": "output_is_two_run_array", "passed": True,
                    "detail": "Output contains at least 2 run results"})
    total_score += 0.5

    # ── Identify ALPHA and BETA runs ─────────────────────────────────────────
    alpha_run = None
    beta_run = None
    for run in output:
        if not isinstance(run, dict):
            continue
        pid = str(run.get("project_id", run.get("project", ""))).upper()
        wp = json.dumps(run).upper()
        if "ALPHA" in pid or "ALPHA-001" in wp or "ALPHA" in wp:
            alpha_run = run
        if "BETA" in pid or "BETA-002" in wp or "BETA" in wp:
            beta_run = run

    # Fallback: assign by index if project_id not set
    if alpha_run is None and len(output) >= 1:
        alpha_run = output[0]
    if beta_run is None and len(output) >= 2:
        beta_run = output[1]

    # ════════════════════════════════════════════════════════════════════════
    # ALPHA-001 CHECKS (valid project — should produce full successful output)
    # ════════════════════════════════════════════════════════════════════════

    REQUIRED_SCHEMA_FIELDS = [
        "today_objective",
        "selected_agent",
        "task_input",
        "expected_output",
        "execution_summary",
        "findings",
        "decisions",
        "next_action",
        "project_card_updates",
        "writeback_payload",
        "safe_to_proceed",
    ]

    # Check 1: All required schema fields present for ALPHA
    if alpha_run:
        missing = [f for f in REQUIRED_SCHEMA_FIELDS if f not in alpha_run]
        if missing:
            checks.append({"name": "alpha_schema_complete", "passed": False,
                            "detail": f"Missing fields in ALPHA run: {missing}"})
        else:
            checks.append({"name": "alpha_schema_complete", "passed": True,
                            "detail": "All required output schema fields present for ALPHA-001"})
            total_score += 1.0
    else:
        checks.append({"name": "alpha_schema_complete", "passed": False,
                        "detail": "ALPHA-001 run not found in output"})

    # Check 2: safe_to_proceed = True for ALPHA
    if alpha_run:
        stp = alpha_run.get("safe_to_proceed")
        passed = stp is True
        checks.append({"name": "alpha_safe_to_proceed_true", "passed": passed,
                        "detail": f"ALPHA safe_to_proceed={stp!r} (expected True)"})
        if passed:
            total_score += 1.0

    # Check 3: next_action is NOT null for ALPHA (hard rule: every successful loop must feed into next)
    if alpha_run:
        na = alpha_run.get("next_action")
        passed = na is not None and str(na).strip() != "" and str(na).lower() != "null"
        checks.append({"name": "alpha_next_action_not_null", "passed": passed,
                        "detail": f"ALPHA next_action={na!r} — must be non-null non-empty string per hard rule 5"})
        if passed:
            total_score += 1.5

    # Check 4: forced_bottleneck override used — today_objective or task_input must reference
    # regulatory data package assembly (the forced bottleneck content)
    if alpha_run:
        run_text = json.dumps(alpha_run).lower()
        regulatory_keywords = ["regulatory", "data package", "partial", "adme", "assemble"]
        forced_keywords_found = sum(1 for kw in regulatory_keywords if kw in run_text)
        passed = forced_keywords_found >= 3
        checks.append({"name": "alpha_forced_bottleneck_respected", "passed": passed,
                        "detail": f"ALPHA run text contains {forced_keywords_found}/5 forced_bottleneck keywords {regulatory_keywords}. Expected ≥3."})
        if passed:
            total_score += 1.5

    # Check 5: Only ONE bottleneck selected (today_objective should be singular, not a list of tasks)
    if alpha_run:
        obj = alpha_run.get("today_objective", "")
        # The today_objective should be a string (not a list), and should not read like multiple parallel goals
        passed = isinstance(obj, str) and len(obj.strip()) > 10
        checks.append({"name": "alpha_today_objective_is_single_string", "passed": passed,
                        "detail": f"today_objective is {'a non-empty string' if passed else 'missing/wrong type/empty'}: {obj!r[:120]}"})
        if passed:
            total_score += 0.5

    # Check 6: findings is a list (not empty ideally, but must be a list)
    if alpha_run:
        findings = alpha_run.get("findings")
        passed = isinstance(findings, list)
        checks.append({"name": "alpha_findings_is_list", "passed": passed,
                        "detail": f"ALPHA findings type: {type(findings).__name__}"})
        if passed:
            total_score += 0.25

    # Check 7: decisions is a list
    if alpha_run:
        decisions = alpha_run.get("decisions")
        passed = isinstance(decisions, list)
        checks.append({"name": "alpha_decisions_is_list", "passed": passed,
                        "detail": f"ALPHA decisions type: {type(decisions).__name__}"})
        if passed:
            total_score += 0.25

    # Check 8: project_card_updates is a dict
    if alpha_run:
        pcu = alpha_run.get("project_card_updates")
        passed = isinstance(pcu, dict)
        checks.append({"name": "alpha_project_card_updates_is_dict", "passed": passed,
                        "detail": f"project_card_updates type: {type(pcu).__name__}"})
        if passed:
            total_score += 0.25

    # Check 9: writeback_payload is a dict
    if alpha_run:
        wp = alpha_run.get("writeback_payload")
        passed = isinstance(wp, dict)
        checks.append({"name": "alpha_writeback_payload_is_dict", "passed": passed,
                        "detail": f"writeback_payload type: {type(wp).__name__}"})
        if passed:
            total_score += 0.25

    # ════════════════════════════════════════════════════════════════════════
    # BETA-002 CHECKS (incomplete project card — must be BLOCKED)
    # ════════════════════════════════════════════════════════════════════════

    # Check 10: safe_to_proceed = False for BETA (missing current_phase triggers failure handling)
    if beta_run:
        stp = beta_run.get("safe_to_proceed")
        passed = stp is False
        checks.append({"name": "beta_safe_to_proceed_false", "passed": passed,
                        "detail": f"BETA safe_to_proceed={stp!r} (expected False — project_card missing current_phase)"})
        if passed:
            total_score += 2.0
    else:
        checks.append({"name": "beta_safe_to_proceed_false", "passed": False,
                        "detail": "BETA-002 run not found in output"})

    # Check 11: BETA run should NOT have a full execution_summary implying actual work was done
    # (agent should stop at BLOCKED — no meaningful execution_summary with actual biotech work)
    if beta_run:
        exec_sum = str(beta_run.get("execution_summary", "")).lower()
        # Must not contain language suggesting actual assay work was done
        bad_phrases = ["selectivity panel", "assay booked", "potency confirmed", "lead compound identified"]
        bad_found = [p for p in bad_phrases if p in exec_sum]
        passed = len(bad_found) == 0
        checks.append({"name": "beta_no_phantom_execution", "passed": passed,
                        "detail": f"BETA execution_summary should not claim work was done on incomplete state. Bad phrases found: {bad_found}"})
        if passed:
            total_score += 0.5

    # ── Final score cap ───────────────────────────────────────────────────────
    total_score = min(total_score, max_score)
    normalized_score = round(total_score / max_score, 4)
    all_passed = all(c["passed"] for c in checks)

    print(json.dumps({
        "passed": all_passed,
        "score": normalized_score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)