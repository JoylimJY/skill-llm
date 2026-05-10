import sys
import json
import math
import traceback
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
passed_all = True

def record(name, passed, detail):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# ── Find the output report ───────────────────────────────────────────────────
report_files = list(workspace.rglob("analysis_report.json"))
if not report_files:
    record("report_file_exists", False, "analysis_report.json not found anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

report_path = report_files[0]
try:
    with open(report_path) as f:
        report = json.load(f)
    record("report_is_valid_json", True, f"Found and parsed {report_path}")
except Exception as e:
    record("report_is_valid_json", False, f"Failed to parse JSON: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ════════════════════════════════════════════════════════════════
# SECTION A: A/B Test Analysis
# ════════════════════════════════════════════════════════════════

try:
    ab = report.get("ab_test_analysis", {})

    # A1: Bonferroni-corrected alpha = 0.05 / 3 ≈ 0.016667
    bonf_alpha = ab.get("bonferroni_alpha")
    expected_bonf = 0.05 / 3
    if bonf_alpha is not None and abs(float(bonf_alpha) - expected_bonf) < 1e-4:
        record("A1_bonferroni_alpha_correct", True,
               f"bonferroni_alpha={bonf_alpha:.6f} ≈ {expected_bonf:.6f}")
    else:
        record("A1_bonferroni_alpha_correct", False,
               f"Expected bonferroni_alpha≈{expected_bonf:.6f}, got {bonf_alpha}")
except Exception as e:
    record("A1_bonferroni_alpha_correct", False, f"Exception: {e}")

try:
    ab = report.get("ab_test_analysis", {})
    # A2: SRM check for subscription_conversion metric
    # total visitors: control=14200, treatment=14350, total=28550
    # expected per arm = 28550/2 = 14275
    # SRM ratio = abs(14200-14350)/14275 = 150/14275 ≈ 0.01051 > 0.01 → SRM detected
    srm = ab.get("srm_detected")
    if srm is True:
        record("A2_srm_detected_correctly", True, "SRM correctly flagged (imbalance > 1%)")
    else:
        record("A2_srm_detected_correctly", False,
               f"Expected srm_detected=True (150/14275≈1.05%>1%), got {srm}")
except Exception as e:
    record("A2_srm_detected_correctly", False, f"Exception: {e}")

try:
    ab = report.get("ab_test_analysis", {})
    metrics_results = ab.get("metrics", {})

    # A3: subscription_conversion significance under Bonferroni
    # p_c = 1423/14200 ≈ 0.10021, p_t = 1612/14350 ≈ 0.11234
    # pooled ≈ 0.10634, se ≈ 0.003648, z ≈ 3.325, p ≈ 0.000887 < 0.016667 → significant
    conv = metrics_results.get("subscription_conversion", {})
    conv_sig = conv.get("significant")
    conv_pval = conv.get("p_value")
    if conv_sig is True and conv_pval is not None and float(conv_pval) < 0.0167:
        record("A3_conversion_significant_bonferroni", True,
               f"subscription_conversion significant under Bonferroni (p={conv_pval:.6f})")
    else:
        record("A3_conversion_significant_bonferroni", False,
               f"Expected significant=True with p<0.0167, got significant={conv_sig}, p={conv_pval}")
except Exception as e:
    record("A3_conversion_significant_bonferroni", False, f"Exception: {e}")

try:
    ab = report.get("ab_test_analysis", {})
    metrics_results = ab.get("metrics", {})

    # A4: 7day_retention significance under Bonferroni
    # p_c = 8900/14200 ≈ 0.6268, p_t = 9180/14350 ≈ 0.6397
    # pooled ≈ 0.6333, se ≈ 0.005716, z ≈ 2.258, p ≈ 0.0239 > 0.016667 → NOT significant
    ret = metrics_results.get("7day_retention", {})
    ret_sig = ret.get("significant")
    ret_pval = ret.get("p_value")
    if ret_sig is False and ret_pval is not None and float(ret_pval) > 0.016:
        record("A4_retention_not_significant_bonferroni", True,
               f"7day_retention correctly NOT significant under Bonferroni (p={ret_pval:.6f})")
    else:
        record("A4_retention_not_significant_bonferroni", False,
               f"Expected significant=False with p>0.0167, got significant={ret_sig}, p={ret_pval}")
except Exception as e:
    record("A4_retention_not_significant_bonferroni", False, f"Exception: {e}")

try:
    ab = report.get("ab_test_analysis", {})
    metrics_results = ab.get("metrics", {})

    # A5: lift values are present and directionally correct
    # subscription_conversion: p_t > p_c → positive lift
    conv = metrics_results.get("subscription_conversion", {})
    lift = conv.get("lift")
    if lift is not None and float(lift) > 0:
        record("A5_lift_positive_for_conversion", True, f"lift={lift:.4f} (positive, correct)")
    else:
        record("A5_lift_positive_for_conversion", False, f"Expected positive lift, got {lift}")
except Exception as e:
    record("A5_lift_positive_for_conversion", False, f"Exception: {e}")

# ════════════════════════════════════════════════════════════════
# SECTION B: Feature Engineering
# ════════════════════════════════════════════════════════════════

try:
    fe = report.get("feature_engineering", {})

    # B1: cyclical time features present
    time_feats = fe.get("time_features_added", [])
    required_time = {"dow_sin", "dow_cos", "month_sin", "month_cos", "is_weekend"}
    got_feats = set(time_feats) if isinstance(time_feats, list) else set()
    if required_time.issubset(got_feats):
        record("B1_cyclical_time_features_present", True,
               f"All cyclical features found: {sorted(got_feats)}")
    else:
        missing = required_time - got_feats
        record("B1_cyclical_time_features_present", False,
               f"Missing cyclical features: {missing}")
except Exception as e:
    record("B1_cyclical_time_features_present", False, f"Exception: {e}")

try:
    fe = report.get("feature_engineering", {})

    # B2: pipeline fit only on train, not full dataset
    fit_on_train_only = fe.get("fit_on_train_only")
    if fit_on_train_only is True:
        record("B2_no_data_leakage", True, "fit_on_train_only=True confirmed")
    else:
        record("B2_no_data_leakage", False,
               f"fit_on_train_only must be True, got {fit_on_train_only}")
except Exception as e:
    record("B2_no_data_leakage", False, f"Exception: {e}")

try:
    fe = report.get("feature_engineering", {})

    # B3: dirty data cleaned (sentinel -999 and negatives handled)
    dirty_cleaned = fe.get("dirty_data_cleaned")
    if dirty_cleaned is True:
        record("B3_dirty_data_cleaned", True, "dirty_data_cleaned=True confirmed")
    else:
        record("B3_dirty_data_cleaned", False,
               f"dirty_data_cleaned must be True, got {dirty_cleaned}")
except Exception as e:
    record("B3_dirty_data_cleaned", False, f"Exception: {e}")

try:
    fe = report.get("feature_engineering", {})

    # B4: train/test split recorded with reasonable sizes
    n_train = fe.get("n_train")
    n_test = fe.get("n_test")
    if n_train and n_test:
        total = int(n_train) + int(n_test)
        if 2500 <= total <= 3000 and int(n_train) > int(n_test):
            record("B4_train_test_split_valid", True,
                   f"n_train={n_train}, n_test={n_test}, total={total}")
        else:
            record("B4_train_test_split_valid", False,
                   f"Unexpected split: n_train={n_train}, n_test={n_test}, total={total}")
    else:
        record("B4_train_test_split_valid", False, f"n_train/n_test missing from report")
except Exception as e:
    record("B4_train_test_split_valid", False, f"Exception: {e}")

# ════════════════════════════════════════════════════════════════
# SECTION C: Model Evaluation
# ════════════════════════════════════════════════════════════════

try:
    me = report.get("model_evaluation", {})

    # C1: AUC-ROC and AUC-PR both reported
    roc = me.get("roc_auc", {})
    pr  = me.get("avg_prec", {})
    roc_mean = roc.get("mean") if isinstance(roc, dict) else None
    pr_mean  = pr.get("mean")  if isinstance(pr,  dict) else None
    if roc_mean is not None and pr_mean is not None:
        record("C1_both_auc_metrics_reported", True,
               f"roc_auc mean={roc_mean:.4f}, avg_prec mean={pr_mean:.4f}")
    else:
        record("C1_both_auc_metrics_reported", False,
               f"roc_auc={roc_mean}, avg_prec={pr_mean}")
except Exception as e:
    record("C1_both_auc_metrics_reported", False, f"Exception: {e}")

try:
    me = report.get("model_evaluation", {})

    # C2: AUC-ROC mean is above 0.5 (beats dummy baseline)
    roc = me.get("roc_auc", {})
    roc_mean = float(roc.get("mean", 0)) if isinstance(roc, dict) else 0
    if roc_mean > 0.5:
        record("C2_model_beats_baseline", True,
               f"ROC-AUC={roc_mean:.4f} > 0.5 (dummy)")
    else:
        record("C2_model_beats_baseline", False,
               f"ROC-AUC={roc_mean:.4f} does not beat dummy classifier")
except Exception as e:
    record("C2_model_beats_baseline", False, f"Exception: {e}")

try:
    me = report.get("model_evaluation", {})

    # C3: overfit_gap reported (from skill's evaluate_model checklist)
    roc = me.get("roc_auc", {})
    overfit_gap = roc.get("overfit_gap") if isinstance(roc, dict) else None
    if overfit_gap is not None:
        flag = overfit_gap > 0.05
        record("C3_overfit_gap_reported", True,
               f"overfit_gap={overfit_gap:.4f}, overfit_warning={flag}")
    else:
        record("C3_overfit_gap_reported", False, "overfit_gap missing from roc_auc section")
except Exception as e:
    record("C3_overfit_gap_reported", False, f"Exception: {e}")

try:
    me = report.get("model_evaluation", {})

    # C4: StratifiedKFold used (5 folds per skill default)
    cv_folds = me.get("cv_folds")
    cv_strategy = me.get("cv_strategy", "")
    if cv_folds == 5 and "stratified" in str(cv_strategy).lower():
        record("C4_stratified_kfold_5_used", True,
               f"cv_folds={cv_folds}, cv_strategy={cv_strategy}")
    else:
        record("C4_stratified_kfold_5_used", False,
               f"Expected cv_folds=5 and stratified strategy, got folds={cv_folds}, strategy={cv_strategy}")
except Exception as e:
    record("C4_stratified_kfold_5_used", False, f"Exception: {e}")

try:
    me = report.get("model_evaluation", {})

    # C5: std (uncertainty) reported for AUC metrics
    roc = me.get("roc_auc", {})
    pr  = me.get("avg_prec", {})
    roc_std = roc.get("std") if isinstance(roc, dict) else None
    pr_std  = pr.get("std")  if isinstance(pr,  dict) else None
    if roc_std is not None and pr_std is not None:
        record("C5_std_reported_for_metrics", True,
               f"roc_auc std={roc_std:.4f}, avg_prec std={pr_std:.4f}")
    else:
        record("C5_std_reported_for_metrics", False,
               f"std missing: roc_auc.std={roc_std}, avg_prec.std={pr_std}")
except Exception as e:
    record("C5_std_reported_for_metrics", False, f"Exception: {e}")

# ── Final score ──────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
passed_all = passed_count == total

print(json.dumps({
    "passed": passed_all,
    "score": score,
    "checks": checks
}, indent=2))