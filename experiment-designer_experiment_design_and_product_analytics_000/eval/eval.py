#!/usr/bin/env python3
"""
Evaluation script for the Experiment Designer task.
Usage: python3 eval_script.py /workspace
"""

import sys
import json
import re
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ── Helper ──────────────────────────────────────────────────────────────
    def find_plan_file(ws):
        """Search for the experiment plan JSON file anywhere in workspace."""
        candidates = list(ws.rglob("experiment_plan.json"))
        return candidates[0] if candidates else None

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Load the plan file ───────────────────────────────────────────────────
    plan_path = find_plan_file(ws)
    if plan_path is None:
        checks.append({"name": "file_exists", "passed": False,
                        "detail": "experiment_plan.json not found anywhere in workspace."})
        return False, 0.0, checks

    try:
        with open(plan_path) as f:
            plan = json.load(f)
    except Exception as e:
        checks.append({"name": "file_parseable", "passed": False,
                        "detail": f"Could not parse experiment_plan.json as JSON: {e}"})
        return False, 0.0, checks

    total_score += add_check("file_exists", True,
                              f"Found experiment_plan.json at {plan_path}")

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 1 – ICE scores computed with correct formula: (I*C*E)/10
    # ════════════════════════════════════════════════════════════════════════
    try:
        experiments = plan.get("experiments", plan.get("experiment_candidates", []))
        assert isinstance(experiments, list) and len(experiments) >= 3

        ice_correct = True
        ice_detail_parts = []
        for exp in experiments:
            name = exp.get("name", exp.get("idea", "unknown"))
            impact     = exp.get("impact",     exp.get("Impact"))
            confidence = exp.get("confidence", exp.get("Confidence"))
            ease       = exp.get("ease",       exp.get("Ease"))
            ice_score  = exp.get("ice_score",  exp.get("ICE_score", exp.get("ice")))

            if None in (impact, confidence, ease, ice_score):
                ice_correct = False
                ice_detail_parts.append(f"  {name}: missing ICE fields")
                continue

            expected = round((float(impact) * float(confidence) * float(ease)) / 10, 4)
            actual   = round(float(ice_score), 4)
            # Allow ±0.15 tolerance for rounding
            if abs(expected - actual) > 0.15:
                ice_correct = False
                ice_detail_parts.append(
                    f"  {name}: expected ICE≈{expected}, got {actual}")
            else:
                ice_detail_parts.append(f"  {name}: ICE={actual} ✓")

        detail = "ICE formula (I*C*E)/10 check:\n" + "\n".join(ice_detail_parts)
        total_score += add_check("ice_formula_correct", ice_correct, detail, weight=2.0)
    except Exception as e:
        total_score += add_check("ice_formula_correct", False,
                                  f"Error checking ICE scores: {e}", weight=2.0)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 2 – Correct top-ranked experiment selected (Idea B: progress bar)
    # Idea B: Impact=6, Confidence=8, Ease=9 → ICE = 432/10 = 43.2
    # Idea A: Impact=8, Confidence=7, Ease=6 → ICE = 336/10 = 33.6
    # Idea C: Impact=9, Confidence=5, Ease=3 → ICE = 135/10 = 13.5
    # ════════════════════════════════════════════════════════════════════════
    try:
        selected_raw = plan.get("selected_experiment",
                        plan.get("top_experiment",
                        plan.get("recommended_experiment", "")))
        selected = str(selected_raw).lower()

        # Look for "B", "progress", "progress bar", "inline progress"
        keywords = ["progress", "inline", "idea b", "idea_b", "experiment b"]
        correct_selection = any(kw in selected for kw in keywords)

        # Also check inside the experiments list for a "selected" flag
        if not correct_selection:
            for exp in experiments:
                if exp.get("selected") or exp.get("recommended"):
                    n = str(exp.get("name", exp.get("idea", ""))).lower()
                    if any(kw in n for kw in keywords):
                        correct_selection = True
                        break

        total_score += add_check(
            "correct_top_experiment_selected",
            correct_selection,
            f"Selected/recommended experiment value: '{selected_raw}'. "
            f"Expected: Idea B (Inline Progress Indicator, ICE=43.2).",
            weight=2.0
        )
    except Exception as e:
        total_score += add_check("correct_top_experiment_selected", False,
                                  f"Error checking selected experiment: {e}", weight=2.0)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 3 – Hypothesis for selected experiment in If/Then/Because format
    # ════════════════════════════════════════════════════════════════════════
    try:
        hypo_text = ""
        # Look for hypothesis at top level or inside the selected experiment entry
        if "hypothesis" in plan:
            hypo_text = str(plan["hypothesis"])
        else:
            for exp in experiments:
                nm = str(exp.get("name", exp.get("idea", ""))).lower()
                if any(kw in nm for kw in ["progress", "inline"]):
                    hypo_text = str(exp.get("hypothesis", ""))
                    break

        hypo_lower = hypo_text.lower()
        has_if      = "if " in hypo_lower or hypo_lower.startswith("if")
        has_then    = "then " in hypo_lower
        has_because = "because " in hypo_lower

        format_ok = has_if and has_then and has_because
        detail_parts = [
            f"  'If': {'✓' if has_if else '✗'}",
            f"  'Then': {'✓' if has_then else '✗'}",
            f"  'Because': {'✓' if has_because else '✗'}",
            f"  Snippet: {hypo_text[:200]!r}",
        ]
        total_score += add_check(
            "hypothesis_if_then_because_format",
            format_ok,
            "Hypothesis structure:\n" + "\n".join(detail_parts),
            weight=1.5
        )
    except Exception as e:
        total_score += add_check("hypothesis_if_then_because_format", False,
                                  f"Error checking hypothesis: {e}", weight=1.5)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 4 – Hypothesis quality checklist: metric + causal reason + MDE
    # ════════════════════════════════════════════════════════════════════════
    try:
        hypo_lower2 = hypo_text.lower()
        # Must mention a metric (conversion, completion, submit, rate)
        metric_mentioned = any(w in hypo_lower2 for w in
                               ["conversion", "completion", "submit", "rate", "drop"])
        # Must mention a numeric magnitude or "2" or "percentage"
        magnitude_mentioned = bool(re.search(r"\d", hypo_text)) or \
                              "percentage" in hypo_lower2 or "point" in hypo_lower2
        # Must contain causal reason
        causal_ok = "because" in hypo_lower2 and len(hypo_text.split("because")[-1].strip()) > 10

        quality_ok = metric_mentioned and magnitude_mentioned and causal_ok
        detail = (
            f"metric_mentioned={metric_mentioned}, "
            f"magnitude_mentioned={magnitude_mentioned}, "
            f"causal_reason_present={causal_ok}"
        )
        total_score += add_check("hypothesis_quality_checklist", quality_ok, detail, weight=1.0)
    except Exception as e:
        total_score += add_check("hypothesis_quality_checklist", False,
                                  f"Error: {e}", weight=1.0)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 5 – Primary metric defined (single), guardrail metrics present
    # ════════════════════════════════════════════════════════════════════════
    try:
        primary   = plan.get("primary_metric",   plan.get("primary_metrics"))
        guardrail = plan.get("guardrail_metrics", plan.get("guardrails", []))

        # primary must be a string (single metric), not a list
        primary_single = isinstance(primary, str) and len(primary.strip()) > 0

        # guardrail must be a non-empty list (or comma-separated string)
        if isinstance(guardrail, list):
            guardrail_present = len(guardrail) >= 1
        elif isinstance(guardrail, str):
            guardrail_present = len(guardrail.strip()) > 0
        else:
            guardrail_present = False

        metrics_ok = primary_single and guardrail_present
        detail = (f"primary_metric={primary!r} (single={primary_single}), "
                  f"guardrail_metrics={guardrail!r} (present={guardrail_present})")
        total_score += add_check("metrics_defined", metrics_ok, detail, weight=1.0)
    except Exception as e:
        total_score += add_check("metrics_defined", False, f"Error: {e}", weight=1.0)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 6 – Sample size calculated using the calculator script
    #           Baseline=0.18, MDE=0.02 absolute → expected ~3842 per variant
    #           (tolerance ±200 per variant to allow minor rounding differences)
    # ════════════════════════════════════════════════════════════════════════
    try:
        ss_section = plan.get("sample_size", plan.get("sample_size_estimate", {}))
        if isinstance(ss_section, dict):
            per_variant = ss_section.get("per_variant",
                          ss_section.get("n_per_variant",
                          ss_section.get("per_variant_n")))
            total_n     = ss_section.get("total",
                          ss_section.get("n_total",
                          ss_section.get("total_n")))
        else:
            per_variant = None
            total_n     = None

        # Run the actual script to get ground truth
        calc_result = subprocess.run(
            ["python3", "scripts/sample_size_calculator.py",
             "--baseline-rate", "0.18",
             "--mde", "0.02",
             "--mde-type", "absolute",
             "--alpha", "0.05",
             "--power", "0.80"],
            capture_output=True, text=True, cwd=workspace
        )
        gt_per = gt_total = None
        for line in calc_result.stdout.splitlines():
            if "Per-variant N" in line:
                gt_per = int(re.search(r"\d+", line).group())
            if "Total N" in line:
                gt_total = int(re.search(r"\d+", line).group())

        if gt_per is None:
            raise RuntimeError("Could not get ground truth from calculator script.")

        per_v_ok = total_ok = False
        if per_variant is not None:
            per_v_ok = abs(int(per_variant) - gt_per) <= 200
        if total_n is not None:
            total_ok = abs(int(total_n) - gt_total) <= 400

        ss_ok = per_v_ok or total_ok
        detail = (f"Ground truth: per_variant={gt_per}, total={gt_total}. "
                  f"Plan has: per_variant={per_variant}, total={total_n}. "
                  f"per_v_ok={per_v_ok}, total_ok={total_ok}")
        total_score += add_check("sample_size_correct", ss_ok, detail, weight=2.0)
    except Exception as e:
        total_score += add_check("sample_size_correct", False,
                                  f"Error checking sample size: {e}", weight=2.0)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 7 – Stopping rules / test parameters documented
    # ════════════════════════════════════════════════════════════════════════
    try:
        stopping = plan.get("stopping_rules",
                   plan.get("test_parameters",
                   plan.get("launch_parameters", {})))
        has_stopping = isinstance(stopping, dict) and len(stopping) > 0
        if not has_stopping and isinstance(stopping, str):
            has_stopping = len(stopping.strip()) > 10

        detail = f"stopping_rules/test_parameters value: {str(stopping)[:200]}"
        total_score += add_check("stopping_rules_present", has_stopping, detail, weight=0.5)
    except Exception as e:
        total_score += add_check("stopping_rules_present", False, f"Error: {e}", weight=0.5)

    # ── Final score ──────────────────────────────────────────────────────────
    max_score = 1.0 + 2.0 + 2.0 + 1.5 + 1.0 + 1.0 + 2.0 + 0.5  # = 11.0
    normalised = round(total_score / max_score, 4)
    passed = normalised >= 0.70 and all(
        c["passed"] for c in checks
        if c["name"] in {"ice_formula_correct", "correct_top_experiment_selected",
                         "hypothesis_if_then_because_format", "sample_size_correct"}
    )
    return passed, normalised, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    passed, score, checks = run_checks(workspace)
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()