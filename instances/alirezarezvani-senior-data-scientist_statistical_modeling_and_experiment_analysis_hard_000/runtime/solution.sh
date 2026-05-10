#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"
cd "$WORKSPACE"

echo "=== Step 1: Locate raw inputs ==="
EXPERIMENT_FILE=$(find "$WORKSPACE/data/raw" -name "experiment_results.json" | head -n 1)
COHORT_FILE=$(find "$WORKSPACE/data/raw" -name "patient_cohort.csv" | head -n 1)
ANALYSIS_CONFIG=$(find "$WORKSPACE/configs" -name "analysis_config.json" | head -n 1)
MODELING_SPEC=$(find "$WORKSPACE/configs" -name "modeling_spec.json" | head -n 1)
SKILL_DIR="/workspace/skill_context"

echo "Experiment data: $EXPERIMENT_FILE"
echo "Cohort data:     $COHORT_FILE"
echo "Analysis config: $ANALYSIS_CONFIG"
echo "Modeling spec:   $MODELING_SPEC"
echo "Skill dir:       $SKILL_DIR"

echo ""
echo "=== Step 2: Part 1 — Experiment Analysis with Bonferroni Correction ==="

cat > /tmp/analyze_experiment.py << 'PYEOF'
import sys
import json
import math
import numpy as np
from scipy import stats

# ── Load inputs ────────────────────────────────────────────────────────────────
with open(sys.argv[1]) as f:
    exp_data = json.load(f)

with open(sys.argv[2]) as f:
    config = json.load(f)

output_path = sys.argv[3]

# ── Parameters from SKILL.md and config ───────────────────────────────────────
base_alpha = config["base_alpha"]          # 0.05
n_secondary = config["n_secondary_metrics"]  # 2
srm_threshold = config["srm_threshold"]    # 0.01
# Total metrics = primary (1) + secondary (2) = 3
n_total_metrics = 1 + n_secondary
# Bonferroni correction: alpha / n_metrics  (from SKILL.md checklist step 7)
corrected_alpha = base_alpha / n_total_metrics

print(f"Base alpha: {base_alpha}")
print(f"Total metrics: {n_total_metrics}")
print(f"Bonferroni corrected alpha: {corrected_alpha:.6f}")

# ── analyze_experiment function from SKILL.md ──────────────────────────────────
def analyze_experiment(control, treatment, alpha=0.05):
    p_c = control["conversions"] / control["visitors"]
    p_t = treatment["conversions"] / treatment["visitors"]
    pooled = (control["conversions"] + treatment["conversions"]) / (
        control["visitors"] + treatment["visitors"]
    )
    se = np.sqrt(
        pooled * (1 - pooled) * (1 / control["visitors"] + 1 / treatment["visitors"])
    )
    z = (p_t - p_c) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    ci_low  = (p_t - p_c) - stats.norm.ppf(1 - alpha / 2) * se
    ci_high = (p_t - p_c) + stats.norm.ppf(1 - alpha / 2) * se
    return {
        "control_rate":   round(p_c, 6),
        "treatment_rate": round(p_t, 6),
        "lift":           round((p_t - p_c) / p_c, 6),
        "p_value":        round(float(p_value), 8),
        "significant":    bool(p_value < alpha),
        "ci_95":          [round(ci_low, 6), round(ci_high, 6)],
        "z_stat":         round(float(z), 6),
    }

# ── Analyze all metrics at corrected alpha ─────────────────────────────────────
results = {}

# Primary metric
primary_key = "primary"
primary = exp_data["metrics"][primary_key]
results[primary["name"]] = {
    "metric_type": "primary",
    **analyze_experiment(primary["control"], primary["treatment"], alpha=corrected_alpha),
    "n_control":   primary["control"]["visitors"],
    "n_treatment": primary["treatment"]["visitors"],
}

# Secondary metrics
for key in ["secondary_1", "secondary_2"]:
    m = exp_data["metrics"][key]
    results[m["name"]] = {
        "metric_type": "secondary",
        **analyze_experiment(m["control"], m["treatment"], alpha=corrected_alpha),
        "n_control":   m["control"]["visitors"],
        "n_treatment": m["treatment"]["visitors"],
    }

# ── Sample Ratio Mismatch check for segments ──────────────────────────────────
# From SKILL.md checklist: abs(n_control - n_treatment) / expected < 0.01
# expected = total / 2 (50/50 split as per exp_data["expected_split"] = 0.5)
srm_results = {}
expected_split = exp_data.get("expected_split", 0.5)

for seg_name, seg_data in exp_data.get("segments", {}).items():
    n_ctrl = seg_data["control"]["visitors"]
    n_trt  = seg_data["treatment"]["visitors"]
    n_total = n_ctrl + n_trt
    n_expected_each = n_total * expected_split
    srm_ratio = abs(n_ctrl - n_expected_each) / n_expected_each
    flagged = srm_ratio > srm_threshold
    srm_results[seg_name] = {
        "n_control":            n_ctrl,
        "n_treatment":          n_trt,
        "n_expected_each":      round(n_expected_each, 1),
        "srm_ratio":            round(float(srm_ratio), 6),
        "srm_threshold":        srm_threshold,
        "sample_ratio_mismatch": flagged,
        "warning": f"FLAGGED: SRM ratio {srm_ratio:.4f} exceeds threshold {srm_threshold}" if flagged else "OK",
    }
    if flagged:
        print(f"[WARNING] SRM detected in segment '{seg_name}': ratio={srm_ratio:.4f}")

# ── Build final output ─────────────────────────────────────────────────────────
output = {
    "experiment_name":   exp_data["experiment_name"],
    "start_date":        exp_data["start_date"],
    "end_date":          exp_data["end_date"],
    "multiple_testing_correction": {
        "method":          "Bonferroni",
        "base_alpha":      base_alpha,
        "n_metrics":       n_total_metrics,
        "corrected_alpha": round(corrected_alpha, 8),
        "note":            "alpha / n_metrics per SKILL.md checklist step 7",
    },
    "metric_results": results,
    "segment_srm_checks": srm_results,
    "summary": {
        "significant_metrics": [
            name for name, r in results.items() if r["significant"]
        ],
        "srm_flagged_segments": [
            seg for seg, r in srm_results.items() if r["sample_ratio_mismatch"]
        ],
    },
}

with open(output_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"Experiment analysis saved to {output_path}")
print(f"Corrected alpha: {corrected_alpha:.6f}")
print(f"Significant metrics: {output['summary']['significant_metrics']}")
print(f"SRM-flagged segments: {output['summary']['srm_flagged_segments']}")
PYEOF

python3 /tmp/analyze_experiment.py \
    "$EXPERIMENT_FILE" \
    "$ANALYSIS_CONFIG" \
    "$WORKSPACE/experiment_analysis.json"

echo ""
echo "=== Step 3: Part 2 — Feature Engineering + Model Evaluation ==="

cat > /tmp/train_evaluate.py << 'PYEOF'
import sys
import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.metrics import make_scorer, roc_auc_score, average_precision_score
import xgboost as xgb

# ── Load inputs ────────────────────────────────────────────────────────────────
cohort_path  = sys.argv[1]
spec_path    = sys.argv[2]
output_path  = sys.argv[3]

df = pd.read_csv(cohort_path)

with open(spec_path) as f:
    spec = json.load(f)

target_col     = spec["target_column"]       # "re_engaged_30d"
date_col       = spec["date_column"]         # "enrollment_date"
id_col         = spec["id_column"]           # "patient_id"
numeric_cols   = spec["numeric_features"]
categorical_cols = spec["categorical_features"]
cv_folds       = spec["cv_folds"]            # 5
overfit_thresh = spec["overfit_gap_threshold"]  # 0.05

print(f"Dataset shape: {df.shape}")
print(f"Target distribution:\n{df[target_col].value_counts()}")

# ── add_time_features() from SKILL.md ─────────────────────────────────────────
def add_time_features(df, date_col):
    """Extract cyclical and lag features from a datetime column. (SKILL.md)"""
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df["dow_sin"]    = np.sin(2 * np.pi * df[date_col].dt.dayofweek / 7)
    df["dow_cos"]    = np.cos(2 * np.pi * df[date_col].dt.dayofweek / 7)
    df["month_sin"]  = np.sin(2 * np.pi * df[date_col].dt.month / 12)
    df["month_cos"]  = np.cos(2 * np.pi * df[date_col].dt.month / 12)
    df["is_weekend"] = (df[date_col].dt.dayofweek >= 5).astype(int)
    return df

# Apply BEFORE split (temporal features don't cause leakage as they're calendar-based)
df = add_time_features(df, date_col)
time_features = ["dow_sin", "dow_cos", "month_sin", "month_cos", "is_weekend"]

# pharmacy_id is high-cardinality (200 levels > 50 threshold) — EXCLUDE per SKILL.md
# Already excluded from spec drop_columns and not in numeric/categorical_cols

# Extend numeric_cols with time features
all_numeric = numeric_cols + time_features

print(f"Numeric features:     {all_numeric}")
print(f"Categorical features: {categorical_cols}")

X = df[all_numeric + categorical_cols].copy()
y = df[target_col].copy()

# ── build_feature_pipeline() from SKILL.md ────────────────────────────────────
def build_feature_pipeline(numeric_cols, categorical_cols):
    numeric_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale",  StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    transformers = [
        ("num", numeric_pipeline, numeric_cols),
        ("cat", categorical_pipeline, categorical_cols),
    ]
    return ColumnTransformer(transformers, remainder="drop")

preprocessor = build_feature_pipeline(all_numeric, categorical_cols)

# ── XGBoost classifier ────────────────────────────────────────────────────────
xgb_model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1,
)

full_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier",   xgb_model),
])

# ── evaluate_model() from SKILL.md ────────────────────────────────────────────
SCORERS = {
    "roc_auc":  make_scorer(roc_auc_score,  needs_proba=True),
    "avg_prec": make_scorer(average_precision_score, needs_proba=True),
}

def evaluate_model(model, X, y, cv=5):
    """Cross-validate and return mean ± std. (SKILL.md)"""
    cv_results = cross_validate(
        model, X, y,
        cv=StratifiedKFold(n_splits=cv, shuffle=True, random_state=42),
        scoring=SCORERS,
        return_train_score=True,
    )
    summary = {}
    for metric in SCORERS:
        test_scores  = cv_results[f"test_{metric}"]
        train_scores = cv_results[f"train_{metric}"]
        overfit_gap  = float(train_scores.mean() - test_scores.mean())
        summary[metric] = {
            "mean":        round(float(test_scores.mean()), 6),
            "std":         round(float(test_scores.std()),  6),
            "overfit_gap": round(overfit_gap, 6),
            "overfit_warning": overfit_gap > 0.05,
        }
        print(f"  {metric}: mean={test_scores.mean():.4f} ± {test_scores.std():.4f}, "
              f"overfit_gap={overfit_gap:.4f}, warning={overfit_gap > 0.05}")
    return summary

print("\nRunning 5-fold stratified cross-validation...")
cv_summary = evaluate_model(full_pipeline, X, y, cv=cv_folds)

# ── Save feature manifest (proves time features were used) ─────────────────────
feature_manifest = {
    "numeric_features":      all_numeric,
    "categorical_features":  categorical_cols,
    "time_features_added":   time_features,
    "excluded_high_cardinality": ["pharmacy_id"],
    "note": "pharmacy_id excluded: 200 unique levels > 50 threshold per SKILL.md",
    "column_details": {
        "dow_sin":    "sine of day-of-week (cyclical encoding)",
        "dow_cos":    "cosine of day-of-week (cyclical encoding)",
        "month_sin":  "sine of month (cyclical encoding)",
        "month_cos":  "cosine of month (cyclical encoding)",
        "is_weekend": "binary flag: 1 if Saturday or Sunday",
    }
}

# ── Build final report ─────────────────────────────────────────────────────────
report = {
    "model": "XGBClassifier",
    "task":  "binary_classification",
    "target": target_col,
    "cv_folds":   cv_folds,
    "stratified": True,
    "cv_strategy": f"StratifiedKFold(n_splits={cv_folds}, shuffle=True, random_state=42)",
    "feature_engineering": feature_manifest,
    "evaluation_metrics": cv_summary,
    "overfit_gap_threshold": overfit_thresh,
    "notes": [
        "AUC-PR reported alongside AUC-ROC for imbalanced dataset per SKILL.md checklist.",
        "overfit_gap > 0.05 triggers warning flag per SKILL.md.",
        "Cyclical time features (dow_sin, dow_cos, month_sin, month_cos, is_weekend) extracted via add_time_features().",
        "pharmacy_id excluded: high-cardinality (200 levels > 50 threshold) per SKILL.md feature engineering checklist.",
        "Preprocessor fit only on training folds via cross_validate (no leakage).",
    ],
}

with open(output_path, "w") as f:
    json.dump(report, f, indent=2)

print(f"\nModel evaluation report saved to {output_path}")
PYEOF

python3 /tmp/train_evaluate.py \
    "$COHORT_FILE" \
    "$MODELING_SPEC" \
    "$WORKSPACE/model_evaluation_report.json"

echo ""
echo "=== Step 4: Verify outputs ==="
echo "--- experiment_analysis.json ---"
python3 -c "
import json
with open('$WORKSPACE/experiment_analysis.json') as f:
    d = json.load(f)
print('Corrected alpha:', d['multiple_testing_correction']['corrected_alpha'])
print('SRM flagged:', d['summary']['srm_flagged_segments'])
print('Significant metrics:', d['summary']['significant_metrics'])
"

echo "--- model_evaluation_report.json ---"
python3 -c "
import json
with open('$WORKSPACE/model_evaluation_report.json') as f:
    d = json.load(f)
metrics = d['evaluation_metrics']
for name, vals in metrics.items():
    print(f'{name}: mean={vals[\"mean\"]:.4f}, std={vals[\"std\"]:.4f}, overfit_gap={vals[\"overfit_gap\"]:.4f}')
"

echo ""
echo "=== Solution complete. Artifacts generated: ==="
ls -lh "$WORKSPACE/experiment_analysis.json" "$WORKSPACE/model_evaluation_report.json"