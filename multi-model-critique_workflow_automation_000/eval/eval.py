#!/usr/bin/env python3
"""
Evaluation script for the multi-model-critique task.
Checks:
1. run_config.json was created with correct structure and complex=true trigger
2. run_orchestration.py was invoked -> run_plan.json artifact exists with correct fields
3. build_round_prompts.py was invoked -> per-model round prompt files exist
4. final_output.json matches output-schema.md with correct weighted scores
5. ops.maxRounds == 4 (proprietary fixed constraint)
6. weighted_score formula is correct: 0.40*acc + 0.25*cov + 0.20*evi + 0.15*act
7. final_output has required fields: final_answer, key_improvements, uncertainties
8. rounds field == 4 in final output
"""
import sys
import json
import math
from pathlib import Path

def find_file(workspace, name):
    matches = list(Path(workspace).rglob(name))
    return matches[0] if matches else None

def score_check(weights_ok, scores):
    """Verify each model's weighted_score is computed correctly."""
    errors = []
    for model, s in scores.items():
        try:
            acc = s["accuracy"]
            cov = s["coverage"]
            evi = s["evidence"]
            act = s["actionability"]
            expected = round(0.40 * acc + 0.25 * cov + 0.20 * evi + 0.15 * act, 6)
            actual   = round(s["weighted_score"], 6)
            if not math.isclose(expected, actual, abs_tol=0.02):
                errors.append(
                    f"Model '{model}': expected weighted_score≈{expected:.4f}, got {actual:.4f}"
                )
        except KeyError as e:
            errors.append(f"Model '{model}' missing key: {e}")
    return errors

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── 1. run_plan.json exists (from run_orchestration.py) ─────────────────
    run_plan_file = find_file(workspace, "run_plan.json")
    if run_plan_file is None:
        checks.append({"name": "run_plan.json exists", "passed": False,
                        "detail": "run_plan.json not found anywhere in workspace"})
    else:
        checks.append({"name": "run_plan.json exists", "passed": True,
                        "detail": str(run_plan_file)})

    # ── 2. run_plan.json structure ──────────────────────────────────────────
    run_plan_ok = False
    run_plan_data = {}
    if run_plan_file:
        try:
            run_plan_data = json.loads(run_plan_file.read_text())
            required_keys = {"run_id", "question", "models", "rounds", "ops", "session_map"}
            missing = required_keys - set(run_plan_data.keys())
            if missing:
                checks.append({"name": "run_plan.json required keys", "passed": False,
                                "detail": f"Missing keys: {missing}"})
            else:
                run_plan_ok = True
                checks.append({"name": "run_plan.json required keys", "passed": True,
                                "detail": "All required keys present"})
        except Exception as e:
            checks.append({"name": "run_plan.json parse", "passed": False,
                            "detail": f"Parse error: {e}"})
    else:
        checks.append({"name": "run_plan.json required keys", "passed": False,
                        "detail": "File not found"})

    # ── 3. run_plan.json rounds == 4 ────────────────────────────────────────
    if run_plan_ok:
        rounds_val = run_plan_data.get("rounds")
        passed = rounds_val == 4
        checks.append({"name": "run_plan.rounds == 4", "passed": passed,
                        "detail": f"rounds={rounds_val} (must be 4 per skill policy)"})

    # ── 4. run_plan.json ops.maxRounds == 4 ─────────────────────────────────
    if run_plan_ok:
        ops = run_plan_data.get("ops", {})
        max_rounds = ops.get("maxRounds")
        passed = max_rounds == 4
        checks.append({"name": "run_plan.ops.maxRounds == 4", "passed": passed,
                        "detail": f"ops.maxRounds={max_rounds} (skill policy: fixed at 4)"})

    # ── 5. run_plan.json has ≥2 models ──────────────────────────────────────
    if run_plan_ok:
        models = run_plan_data.get("models", [])
        passed = isinstance(models, list) and len(models) >= 2
        checks.append({"name": "run_plan.models >= 2", "passed": passed,
                        "detail": f"models list: {models}"})

    # ── 6. Per-model round prompt files exist (from build_round_prompts.py) ──
    prompt_files = list(Path(workspace).rglob("*_round1.txt"))
    passed = len(prompt_files) >= 2
    checks.append({"name": "per-model round1 prompt files (>=2)", "passed": passed,
                    "detail": f"Found {len(prompt_files)} *_round1.txt files: {[str(f) for f in prompt_files]}"})

    all_four_rounds = True
    if run_plan_ok:
        models = run_plan_data.get("models", [])
        for model in models:
            safe = model.replace("/", "_").replace(":", "_")
            for rnd in range(1, 5):
                matches = list(Path(workspace).rglob(f"{safe}_round{rnd}.txt"))
                if not matches:
                    all_four_rounds = False
                    break
    checks.append({"name": "all 4 rounds prompt files exist per model", "passed": all_four_rounds,
                    "detail": "Each model should have round1..round4 prompt files"})

    # ── 7. final_output.json exists ─────────────────────────────────────────
    final_output_file = find_file(workspace, "final_output.json")
    if final_output_file is None:
        checks.append({"name": "final_output.json exists", "passed": False,
                        "detail": "final_output.json not found anywhere in workspace"})
        # Can't proceed with further checks
        total = sum(c["passed"] for c in checks)
        score = round(total / len(checks), 3)
        print(json.dumps({"passed": score >= 0.6, "score": score, "checks": checks}))
        return

    checks.append({"name": "final_output.json exists", "passed": True,
                    "detail": str(final_output_file)})

    # ── 8. final_output.json parse ───────────────────────────────────────────
    try:
        fo = json.loads(final_output_file.read_text())
    except Exception as e:
        checks.append({"name": "final_output.json parse", "passed": False,
                        "detail": f"Parse error: {e}"})
        total = sum(c["passed"] for c in checks)
        score = round(total / len(checks), 3)
        print(json.dumps({"passed": score >= 0.6, "score": score, "checks": checks}))
        return

    checks.append({"name": "final_output.json parse", "passed": True, "detail": "Valid JSON"})

    # ── 9. final_output rounds == 4 ─────────────────────────────────────────
    fo_rounds = fo.get("rounds")
    passed = fo_rounds == 4
    checks.append({"name": "final_output.rounds == 4", "passed": passed,
                    "detail": f"rounds={fo_rounds}"})

    # ── 10. final_output.ops.maxRounds == 4 ─────────────────────────────────
    fo_ops = fo.get("ops", {})
    fo_max_rounds = fo_ops.get("maxRounds")
    if fo_max_rounds is not None:
        passed = fo_max_rounds == 4
        checks.append({"name": "final_output.ops.maxRounds == 4", "passed": passed,
                        "detail": f"ops.maxRounds={fo_max_rounds}"})
    else:
        # ops is optional in final_output but if present maxRounds must be 4
        checks.append({"name": "final_output.ops.maxRounds == 4", "passed": True,
                        "detail": "ops not present in final_output (optional field)"})

    # ── 11. scores section with correct formula ──────────────────────────────
    scores = fo.get("scores", {})
    if not scores:
        checks.append({"name": "final_output.scores non-empty", "passed": False,
                        "detail": "scores field is missing or empty"})
        checks.append({"name": "weighted_score formula correct", "passed": False,
                        "detail": "Cannot verify: no scores"})
    else:
        checks.append({"name": "final_output.scores non-empty", "passed": True,
                        "detail": f"scores for models: {list(scores.keys())}"})
        formula_errors = score_check(True, scores)
        passed = len(formula_errors) == 0
        checks.append({"name": "weighted_score formula correct (0.40/0.25/0.20/0.15)", "passed": passed,
                        "detail": "; ".join(formula_errors) if formula_errors else
                                  "All weighted_scores match formula"})

    # ── 12. score values in [1,5] range ─────────────────────────────────────
    range_errors = []
    for model, s in scores.items():
        for dim in ["accuracy", "coverage", "evidence", "actionability"]:
            val = s.get(dim)
            if val is not None and not (1 <= val <= 5):
                range_errors.append(f"{model}.{dim}={val} out of [1,5]")
    passed = len(range_errors) == 0
    checks.append({"name": "all score dimensions in [1,5]", "passed": passed,
                    "detail": "; ".join(range_errors) if range_errors else "All in range"})

    # ── 13. final_output section has required fields ─────────────────────────
    fo_out = fo.get("final_output", {})
    required_out_keys = {"final_answer", "key_improvements", "uncertainties"}
    missing_out = required_out_keys - set(fo_out.keys())
    passed = len(missing_out) == 0
    checks.append({"name": "final_output.final_output required fields", "passed": passed,
                    "detail": f"Missing: {missing_out}" if missing_out else
                              "final_answer, key_improvements, uncertainties present"})

    # ── 14. key_improvements and uncertainties are non-empty arrays ──────────
    ki = fo_out.get("key_improvements", [])
    unc = fo_out.get("uncertainties", [])
    passed = isinstance(ki, list) and len(ki) >= 1 and isinstance(unc, list) and len(unc) >= 1
    checks.append({"name": "key_improvements and uncertainties non-empty", "passed": passed,
                    "detail": f"key_improvements len={len(ki)}, uncertainties len={len(unc)}"})

    # ── 15. question field references hospital/protocol topic ─────────────────
    question_text = fo.get("question", "").lower()
    topic_keywords = ["protocol", "anticoagulant", "doac", "heparin", "hospital",
                      "treatment", "clinical", "cardiology", "formulary"]
    found_kw = [kw for kw in topic_keywords if kw in question_text]
    passed = len(found_kw) >= 1
    checks.append({"name": "question field relates to hospital protocol review", "passed": passed,
                    "detail": f"Matching keywords: {found_kw}"})

    # ── 16. complex trigger present in run config ────────────────────────────
    run_config_file = find_file(workspace, "run_config.json")
    if run_config_file:
        try:
            rc = json.loads(run_config_file.read_text())
            complex_val = rc.get("complex")
            passed = complex_val is True or str(complex_val).lower() in ("true", "1", "yes")
            checks.append({"name": "run_config.complex == true", "passed": passed,
                            "detail": f"complex={complex_val}"})
        except Exception as e:
            checks.append({"name": "run_config.complex == true", "passed": False,
                            "detail": f"Parse error: {e}"})
    else:
        # run_config might be embedded; check if question in run_plan was populated
        checks.append({"name": "run_config.complex == true", "passed": run_plan_ok,
                        "detail": "run_config.json not separately found; run_plan presence used as proxy"})

    # ── Final scoring ────────────────────────────────────────────────────────
    total_passed = sum(c["passed"] for c in checks)
    total_checks = len(checks)
    score = round(total_passed / total_checks, 3)
    overall_passed = score >= 0.75

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()