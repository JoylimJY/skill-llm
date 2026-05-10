#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="${1:-/workspace}"
cd "$WORKSPACE"

echo "=== Step 1: Locate all input files ==="
EXPERIMENT_FILE=$(find "$WORKSPACE/data/raw/experiment" -name "*.json" | head -n 1)
USER_CSV=$(find "$WORKSPACE/data/raw/users" -name "*.csv" | head -n 1)
FEATURE_META=$(find "$WORKSPACE/data/raw/users" -name "feature_metadata.json" | head -n 1)

echo "  experiment : $EXPERIMENT_FILE"
echo "  user csv   : $USER_CSV"
echo "  feat meta  : $FEATURE_META"

echo "=== Step 2: Locate skill scripts ==="
SKILL_DIR="/workspace/skill_context"
ls "$SKILL_DIR/scripts/"

echo "=== Step 3: Write the bridge/solution script ==="
cat > /tmp/solve_all.py << 'PYEOF'
import sys
import json
import math
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.metrics import make_scorer, roc_auc_score, average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
import xgboost as xgb

# ── Paths from environment ────────────────────────────────────────────────────
WORKSPACE   = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
EXP_FILE    = list(WORKSPACE.rglob("ab_experiment_q2.json"))[0]
USER_CSV    = list(WORKSPACE.rglob("user_activity_messy.csv"))[0]
META_FILE   = list(WORKSPACE.rglob("feature_metadata.json"))[0]

# ════════════════════════════════════════════════════════════════════════════
# SECTION A: A/B Experiment Analysis  (from SKILL.md §1)
# ════════════════════════════════════════════════════════════════════════════

def analyze_experiment(control, treatment, alpha=0.05):
    """Two-proportion z-test per SKILL.md — exact implementation."""
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
        "lift":        (p_t - p_c) / p_c,
        "p_value":     p_value,
        "significant": p_value < alpha,
        "ci_95":       [ci_low, ci_high],
    }

with open(EXP_FILE) as f:
    exp = json.load(f)

n_metrics = exp["n_metrics"]                     # 3
bonferroni_alpha = 0.05 / n_metrics              # ≈ 0.016667  (PROPRIETARY TRAP)

# SRM check: abs(n_control - n_treatment) / expected < 0.01
all_visitors = sum(m["control"]["visitors"] + m["treatment"]["visitors"]
                   for m in exp["metrics"]) / n_metrics   # per metric expected total
# use first metric for the SRM check (all share the same visitor pool)
first = exp["metrics"][0]
n_control   = first["control"]["visitors"]    # 14200
n_treatment = first["treatment"]["visitors"]  # 14350
total_vis   = n_control + n_treatment          # 28550
expected_per_arm = total_vis / 2               # 14275
srm_ratio   = abs(n_control - n_treatment) / expected_per_arm  # ≈ 0.01051
srm_detected = srm_ratio > 0.01               # True  (PROPRIETARY TRAP)

metrics_results = {}
for metric in exp["metrics"]:
    result = analyze_experiment(
        metric["control"],
        metric["treatment"],
        alpha=bonferroni_alpha,               # corrected alpha
    )
    metrics_results[metric["name"]] = result

ab_section = {
    "bonferroni_alpha":  bonferroni_alpha,
    "n_metrics":         n_metrics,
    "srm_ratio":         srm_ratio,
    "srm_detected":      srm_detected,
    "metrics":           metrics_results,
}

print(f"[AB] Bonferroni alpha = {bonferroni_alpha:.6f}")
print(f"[AB] SRM detected = {srm_detected} (ratio={srm_ratio:.5f})")
for name, res in metrics_results.items():
    print(f"[AB] {name}: p={res['p_value']:.4f}, sig={res['significant']}, lift={res['lift']:.4f}")

# ════════════════════════════════════════════════════════════════════════════
# SECTION B: Feature Engineering  (from SKILL.md §2)
# ════════════════════════════════════════════════════════════════════════════

with open(META_FILE) as f:
    meta = json.load(f)

numeric_cols     = meta["numeric_cols"]
categorical_cols = meta["categorical_cols"]
date_col         = meta["date_col"]
target_col       = meta["target_col"]

df = pd.read_csv(USER_CSV)

# --- Clean dirty data as instructed ---
# Replace sentinel -999 and negative numeric values with NaN
for col in numeric_cols:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: np.nan if (pd.notna(x) and (x == -999 or x < 0)) else x)

# Normalise categoricals: lowercase, empty → NaN
for col in categorical_cols:
    if col in df.columns:
        df[col] = df[col].str.strip().str.lower().replace("", np.nan)

dirty_cleaned = True

# --- Add time features per SKILL.md §2 add_time_features() ---
def add_time_features(df, date_col):
    """Exact implementation from SKILL.md."""
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df["dow_sin"]    = np.sin(2 * np.pi * df[date_col].dt.dayofweek / 7)
    df["dow_cos"]    = np.cos(2 * np.pi * df[date_col].dt.dayofweek / 7)
    df["month_sin"]  = np.sin(2 * np.pi * df[date_col].dt.month / 12)
    df["month_cos"]  = np.cos(2 * np.pi * df[date_col].dt.month / 12)
    df["is_weekend"] = (df[date_col].dt.dayofweek >= 5).astype(int)
    return df

df = add_time_features(df, date_col)
time_features_added = ["dow_sin", "dow_cos", "month_sin", "month_cos", "is_weekend"]

# Extended numeric cols include cyclical features
extended_numeric = numeric_cols + time_features_added

# --- Train/test split BEFORE fitting (SKILL.md checklist item 1) ---
X = df[extended_numeric + categorical_cols]
y = df[target_col]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
n_train = len(X_train)
n_test  = len(X_test)

# --- Build pipeline per SKILL.md build_feature_pipeline() ---
# sparse_output=False is explicitly set in SKILL.md (PROPRIETARY TRAP)
numeric_pipeline = Pipeline([
    ("impute", SimpleImputer(strategy="median")),
    ("scale",  StandardScaler()),
])
categorical_pipeline = Pipeline([
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])
ct = ColumnTransformer([
    ("num", numeric_pipeline, extended_numeric),
    ("cat", categorical_pipeline, categorical_cols),
], remainder="drop")

# Fit ONLY on train (SKILL.md checklist: never fit on full dataset)
ct.fit(X_train)
X_train_tf = ct.transform(X_train)
X_test_tf  = ct.transform(X_test)

fe_section = {
    "time_features_added":  time_features_added,
    "fit_on_train_only":    True,        # confirms no leakage
    "dirty_data_cleaned":   dirty_cleaned,
    "n_train":              n_train,
    "n_test":               n_test,
    "n_features_after_transform": X_train_tf.shape[1],
}

print(f"[FE] n_train={n_train}, n_test={n_test}")
print(f"[FE] features after transform: {X_train_tf.shape[1]}")

# ════════════════════════════════════════════════════════════════════════════
# SECTION C: Model Evaluation  (from SKILL.md §3)
# ════════════════════════════════════════════════════════════════════════════

SCORERS = {
    "roc_auc":  make_scorer(roc_auc_score, needs_proba=True),
    "avg_prec": make_scorer(average_precision_score, needs_proba=True),
}

def evaluate_model(model, X, y, cv=5):
    """Exact implementation from SKILL.md evaluate_model()."""
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
        summary[metric] = {
            "mean":        test_scores.mean(),
            "std":         test_scores.std(),
            # overfit_gap: SKILL.md checklist item 2
            "overfit_gap": train_scores.mean() - test_scores.mean(),
        }
    return summary

model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=4,
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42,
    verbosity=0,
)

cv_summary = evaluate_model(model, X_train_tf, y_train.values, cv=5)

me_section = {
    "cv_folds":    5,
    "cv_strategy": "StratifiedKFold",
    "roc_auc": {
        "mean":        cv_summary["roc_auc"]["mean"],
        "std":         cv_summary["roc_auc"]["std"],
        "overfit_gap": cv_summary["roc_auc"]["overfit_gap"],
        "overfit_warning": cv_summary["roc_auc"]["overfit_gap"] > 0.05,
    },
    "avg_prec": {
        "mean":        cv_summary["avg_prec"]["mean"],
        "std":         cv_summary["avg_prec"]["std"],
        "overfit_gap": cv_summary["avg_prec"]["overfit_gap"],
    },
}

print(f"[ME] ROC-AUC: mean={me_section['roc_auc']['mean']:.4f}, "
      f"std={me_section['roc_auc']['std']:.4f}, "
      f"overfit_gap={me_section['roc_auc']['overfit_gap']:.4f}")
print(f"[ME] AVG-PREC: mean={me_section['avg_prec']['mean']:.4f}")

# ════════════════════════════════════════════════════════════════════════════
# Combine & write final report
# ════════════════════════════════════════════════════════════════════════════

report = {
    "ab_test_analysis":    ab_section,
    "feature_engineering": fe_section,
    "model_evaluation":    me_section,
}

out_path = WORKSPACE / "analysis_report.json"
with open(out_path, "w") as f:
    json.dump(report, f, indent=2, default=float)

print(f"\n✓ analysis_report.json written to {out_path}")
PYEOF

echo "=== Step 4: Execute bridge script ==="
python3 /tmp/solve_all.py "$WORKSPACE"

echo "=== Step 5: Verify output ==="
python3 -c "
import json, sys
with open('$WORKSPACE/analysis_report.json') as f:
    r = json.load(f)
keys = list(r.keys())
print('Top-level keys:', keys)
assert 'ab_test_analysis' in keys
assert 'feature_engineering' in keys
assert 'model_evaluation' in keys
print('Output structure: OK')
"

echo "=== Solution complete. analysis_report.json generated. ==="