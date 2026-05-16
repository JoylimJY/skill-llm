import sys
import json
import math
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score_weights = []

def check(name, condition, detail, weight=1.0):
    checks.append({"name": name, "passed": bool(condition), "detail": str(detail)})
    score_weights.append((bool(condition), weight))

# ─── Find the output file ───────────────────────────────────────────────────
report_files = list(workspace.rglob("validation_report.json"))

if not report_files:
    check("output_file_exists", False, "validation_report.json not found anywhere in workspace", weight=3)
    result = {
        "passed": False,
        "score": 0.0,
        "checks": checks,
    }
    print(json.dumps(result))
    sys.exit(0)

report_path = report_files[0]

try:
    report = json.loads(report_path.read_text())
except Exception as e:
    check("output_file_exists", False, f"Found file but failed to parse JSON: {e}", weight=3)
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

check("output_file_exists", True, f"Found at {report_path}", weight=1)

# ─── CHECK 1: Sample size assessment ───────────────────────────────────────
try:
    # Valid trades after dropping bad rows: T007(err), T022(None), T055(N/A date), T099(empty shares)
    # 143 - 4 bad = 139 valid. 139 >= 100 (preferred) but < 200 (high confidence)
    ss = report.get("sample_size_analysis", {})
    valid_trades = ss.get("valid_trade_count", 0)
    # Accept range 135-143 (different cleaning strategies)
    correct_count = 100 <= valid_trades <= 200
    check("sample_size_valid_trade_count", correct_count,
          f"valid_trade_count={valid_trades}, expected ~139 (100-200 range)", weight=1.5)

    confidence_tier = str(ss.get("confidence_tier", "")).lower()
    # Must be "preferred" (100-199), NOT "high_confidence" (200+), NOT "minimum" (<30)
    tier_ok = "preferred" in confidence_tier or "100" in confidence_tier
    check("sample_size_tier_preferred", tier_ok,
          f"confidence_tier='{confidence_tier}', expected 'preferred' (100-199 range)", weight=1.5)

    meets_min = ss.get("meets_minimum_30", True)
    check("sample_size_meets_minimum", bool(meets_min),
          f"meets_minimum_30={meets_min}", weight=0.5)
except Exception as e:
    check("sample_size_analysis", False, f"Exception reading sample_size_analysis: {e}", weight=3)

# ─── CHECK 2: Stop-loss sensitivity — must identify PLATEAU ────────────────
try:
    sl_sens = report.get("parameter_sensitivity", {}).get("stop_loss", {})
    
    # Must have tested all 5 multipliers: 0.50, 0.75, 1.00, 1.25, 1.50
    tested_mults = sl_sens.get("multipliers_tested", [])
    expected_sl_mults = {0.50, 0.75, 1.00, 1.25, 1.50}
    tested_set = set(float(x) for x in tested_mults)
    sl_mults_ok = expected_sl_mults == tested_set or expected_sl_mults.issubset(tested_set)
    check("sl_sensitivity_correct_multipliers", sl_mults_ok,
          f"SL multipliers tested: {sorted(tested_set)}, expected {sorted(expected_sl_mults)}", weight=2)

    # All SL variations are profitable → plateau
    sl_shape = str(sl_sens.get("shape", "")).lower()
    sl_plateau = "plateau" in sl_shape
    check("sl_sensitivity_plateau_detected", sl_plateau,
          f"SL shape='{sl_shape}', expected 'plateau' (all multipliers profitable)", weight=2)

    # profitable_count should be 5 (all)
    sl_profitable = sl_sens.get("profitable_count", 0)
    check("sl_sensitivity_all_profitable", int(sl_profitable) == 5,
          f"SL profitable_count={sl_profitable}, expected 5", weight=1)
except Exception as e:
    check("sl_sensitivity_analysis", False, f"Exception: {e}", weight=5)

# ─── CHECK 3: Profit-target sensitivity — must identify SPIKE ──────────────
try:
    pt_sens = report.get("parameter_sensitivity", {}).get("profit_target", {})

    # Must have tested all 5 multipliers: 0.80, 0.90, 1.00, 1.10, 1.20
    tested_pt = pt_sens.get("multipliers_tested", [])
    expected_pt_mults = {0.80, 0.90, 1.00, 1.10, 1.20}
    tested_pt_set = set(float(x) for x in tested_pt)
    pt_mults_ok = expected_pt_mults == tested_pt_set or expected_pt_mults.issubset(tested_pt_set)
    check("pt_sensitivity_correct_multipliers", pt_mults_ok,
          f"PT multipliers tested: {sorted(tested_pt_set)}, expected {sorted(expected_pt_mults)}", weight=2)

    # Profitable only near baseline → spike
    pt_shape = str(pt_sens.get("shape", "")).lower()
    pt_spike = "spike" in pt_shape or "fragile" in pt_shape or "narrow" in pt_shape
    check("pt_sensitivity_spike_detected", pt_spike,
          f"PT shape='{pt_shape}', expected 'spike'/'fragile'/'narrow'", weight=2)

    # Only 1-2 profitable (baseline + maybe 1 neighbor)
    pt_profitable = pt_sens.get("profitable_count", 0)
    check("pt_sensitivity_few_profitable", int(pt_profitable) <= 2,
          f"PT profitable_count={pt_profitable}, expected <=2 (spike pattern)", weight=1.5)
except Exception as e:
    check("pt_sensitivity_analysis", False, f"Exception: {e}", weight=5.5)

# ─── CHECK 4: Walk-forward OOS validation ──────────────────────────────────
try:
    wf = report.get("walk_forward_analysis", {})

    # OOS net_pnl = 2100, IS net_pnl = 5800 → ratio = 36.2% < 50% threshold
    oos_ratio = wf.get("oos_to_is_ratio", None)
    if oos_ratio is not None:
        ratio_val = float(oos_ratio)
        ratio_correct = 0.30 <= ratio_val <= 0.42   # 36% ± tolerance
        check("wf_oos_ratio_correct", ratio_correct,
              f"OOS/IS ratio={ratio_val:.3f}, expected ~0.362 (2100/5800)", weight=1.5)
    else:
        check("wf_oos_ratio_correct", False, "oos_to_is_ratio field missing", weight=1.5)

    # Must flag that OOS < 50% threshold → warning
    oos_warning = wf.get("oos_below_50pct_threshold", None)
    if oos_warning is None:
        # Accept string description
        warning_text = str(wf.get("warning", "") + wf.get("assessment", "")).lower()
        oos_warning_flagged = "50" in warning_text or "below" in warning_text or "warning" in warning_text
    else:
        oos_warning_flagged = bool(oos_warning)
    check("wf_oos_below_50pct_flagged", oos_warning_flagged,
          f"Must flag OOS<50% of IS as warning sign per methodology", weight=2)

    # Parameter re-optimization needed flag should be noted
    reopt = wf.get("parameter_reoptimization_flagged", None)
    if reopt is None:
        reopt_text = str(wf.get("notes", "") + wf.get("concerns", "")).lower()
        reopt_flagged = "reoptim" in reopt_text or "re-optim" in reopt_text or "frequent" in reopt_text
    else:
        reopt_flagged = bool(reopt)
    check("wf_reoptimization_flagged", reopt_flagged,
          f"Walk-forward data shows parameter_reoptimization_needed=True, must be noted", weight=1)
except Exception as e:
    check("walk_forward_analysis", False, f"Exception: {e}", weight=4.5)

# ─── CHECK 5: Year-by-year regime analysis ─────────────────────────────────
try:
    regime = report.get("regime_analysis", {})

    # 2 losing years out of 6 → not majority profitable but majority is (4/6 = 67%)
    positive_years = regime.get("positive_years", 0)
    total_years = regime.get("total_years", 0)
    # Correct: 4 positive (2018, 2019, 2021, 2023), 2 negative (2020, 2022)
    years_ok = int(positive_years) == 4 and int(total_years) == 6
    check("regime_year_counts_correct", years_ok,
          f"positive_years={positive_years}, total_years={total_years}, expected 4/6", weight=1.5)

    # Strategy doesn't rely on 1-2 exceptional periods → check note
    majority_positive = regime.get("majority_of_years_positive", None)
    if majority_positive is None:
        regime_text = str(regime.get("assessment", "") + regime.get("notes", "")).lower()
        majority_ok = "majority" in regime_text or "4" in regime_text
    else:
        majority_ok = bool(majority_positive)
    check("regime_majority_positive_years", majority_ok,
          f"Must confirm majority (4/6) of years are positive", weight=1)
except Exception as e:
    check("regime_analysis", False, f"Exception: {e}", weight=2.5)

# ─── CHECK 6: Slippage concern flagged ─────────────────────────────────────
try:
    slippage = report.get("slippage_analysis", {})
    # Input metadata says slippage_model = "conservative_1x" — SKILL.md requires 1.5-2x
    # Agent must flag this as insufficient
    insufficient_slippage = slippage.get("current_model_insufficient", None)
    if insufficient_slippage is None:
        slip_text = str(slippage.get("concern", "") + slippage.get("recommendation", "") +
                       slippage.get("assessment", "")).lower()
        slip_flagged = ("1.5" in slip_text or "2x" in slip_text or "insufficient" in slip_text
                        or "increase" in slip_text or "pessimist" in slip_text)
    else:
        slip_flagged = bool(insufficient_slippage)
    check("slippage_1x_flagged_as_insufficient", slip_flagged,
          f"Slippage model is 1x (conservative_1x), SKILL.md requires 1.5-2x. Must be flagged.", weight=2)
except Exception as e:
    check("slippage_analysis", False, f"Exception: {e}", weight=2)

# ─── CHECK 7: Final decision ────────────────────────────────────────────────
try:
    decision = str(report.get("decision", "")).upper()
    rationale = str(report.get("rationale", "") + report.get("decision_rationale", "")).lower()

    # Expected: ABANDON or REFINE (NOT Deploy)
    # Reasons: OOS < 50%, profit-target spike (fragile), slippage under-tested
    # SL plateau is good, sample size ok, but OOS failure + PT spike + slippage concern → at best REFINE, likely ABANDON
    not_deploy = "DEPLOY" not in decision
    check("decision_not_deploy", not_deploy,
          f"decision='{decision}', should NOT be DEPLOY given OOS<50% and PT spike", weight=2.5)

    valid_decision = "ABANDON" in decision or "REFINE" in decision
    check("decision_is_abandon_or_refine", valid_decision,
          f"decision='{decision}', expected ABANDON or REFINE", weight=2)

    # Rationale must mention key failure modes
    rationale_mentions_oos = "oos" in rationale or "out-of-sample" in rationale or "out of sample" in rationale or "walk" in rationale
    check("rationale_mentions_oos_failure", rationale_mentions_oos,
          f"Rationale must mention OOS/walk-forward failure. Got: '{rationale[:200]}'", weight=1)

    rationale_mentions_pt = ("profit" in rationale and ("spike" in rationale or "fragile" in rationale or "narrow" in rationale or "sensitive" in rationale))
    check("rationale_mentions_pt_spike", rationale_mentions_pt,
          f"Rationale must mention profit-target spike/fragility. Got: '{rationale[:200]}'", weight=1)
except Exception as e:
    check("decision_analysis", False, f"Exception: {e}", weight=6.5)

# ─── Scoring ────────────────────────────────────────────────────────────────
total_weight = sum(w for _, w in score_weights)
earned_weight = sum(w for passed, w in score_weights if passed)
score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0
passed_overall = score >= 0.70

result = {
    "passed": passed_overall,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, indent=2))