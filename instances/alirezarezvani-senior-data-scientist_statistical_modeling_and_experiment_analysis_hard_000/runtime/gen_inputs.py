import os
import json
import random
import numpy as np
import pandas as pd
from pathlib import Path

random.seed(42)
np.random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure with distractors ──────────────────────────────────────
dirs = [
    "data/raw",
    "data/processed",
    "data/external",
    "reports/q1",
    "reports/q2",
    "models/archived",
    "models/candidates",
    "configs",
    "logs",
    "notebooks",
    "src/utils",
    "src/transforms",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractor_files = {
    "configs/old_model_params.yaml": "learning_rate: 0.01\nn_estimators: 50\nmax_depth: 3\n",
    "configs/db_connection.cfg": "[database]\nhost=prod-db.internal\nport=5432\ndbname=health_records\n",
    "logs/training_run_2023_q4.log": "INFO 2023-12-01 model training complete\nWARN 2023-12-01 overfit detected\nERROR 2023-12-02 null values in feature matrix\n",
    "logs/pipeline_errors.log": "KeyError: 'patient_id'\nValueError: could not convert string to float\n",
    "reports/q1/summary.txt": "Q1 2024 Summary\nPatients enrolled: 12034\nDropout rate: 8.2%\n",
    "reports/q2/kpi_dashboard.csv": "metric,value\nDAU,4521\nMAU,18200\nretention_7d,0.62\n",
    "notebooks/eda_scratch.py": "# TODO: clean this up\nimport pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df.head())\n",
    "src/utils/helpers.py": "def normalize(x):\n    return (x - x.min()) / (x.max() - x.min())\n",
    "src/transforms/legacy_encoder.py": "# Deprecated - use sklearn pipeline instead\nclass OldEncoder:\n    pass\n",
    "models/archived/baseline_v1.pkl": b'\x80\x05\x95\x05\x00\x00\x00\x00\x00\x00\x00\x8c\x04None\x94.',
    "data/external/icd10_codes.csv": "code,description\nZ79.4,Long-term insulin use\nZ87.891,Personal history of nicotine dependence\n",
    "data/processed/stale_features_v0.parquet": None,  # will create empty file
}

for filepath, content in distractor_files.items():
    full_path = WORKSPACE / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    if content is None:
        full_path.write_bytes(b"")
    elif isinstance(content, bytes):
        full_path.write_bytes(content)
    else:
        full_path.write_text(content)

# ── Generate experiment data (A/B test results with intentional messiness) ────
# The experiment tested a push-notification intervention on medication adherence.
# There are 3 metrics: primary (adherence_rate) + 2 secondary (app_open_rate, refill_rate)
# Importantly: sample ratio mismatch check MUST be performed (groups differ slightly)
# The control and treatment sizes differ by ~0.8% (within threshold) for primary,
# but a second "segment" has >1% SRM that must be caught.

experiment_data = {
    "experiment_name": "medication_adherence_push_v3",
    "start_date": "2024-01-08",
    "end_date": "2024-01-22",
    "description": "14-day push notification intervention for medication adherence",
    "expected_split": 0.5,
    "metrics": {
        "primary": {
            "name": "adherence_rate",
            "control": {"conversions": 1823, "visitors": 18200},
            "treatment": {"conversions": 1998, "visitors": 18050}
        },
        "secondary_1": {
            "name": "app_open_rate",
            "control": {"conversions": 9120, "visitors": 18200},
            "treatment": {"conversions": 9541, "visitors": 18050}
        },
        "secondary_2": {
            "name": "refill_rate",
            "control": {"conversions": 4105, "visitors": 18200},
            "treatment": {"conversions": 4389, "visitors": 18050}
        }
    },
    "segments": {
        "diabetic_patients": {
            "control": {"conversions": 412, "visitors": 3800},
            "treatment": {"conversions": 487, "visitors": 4250}
            # Note: 3800 + 4250 = 8050 total, expected ~50/50 = 4025 each
            # SRM: abs(3800 - 4025) / 4025 = 225/4025 ≈ 0.0559 >> 0.01 → FLAGGED
        }
    }
}

with open(WORKSPACE / "data/raw/experiment_results.json", "w") as f:
    json.dump(experiment_data, f, indent=2)

# ── Generate patient behavioral dataset for feature engineering + modeling ────
# 5000 patients, messy: missing values, skewed numerics, date column, high-cardinality cat
np.random.seed(42)
n = 5000

enrollment_dates = pd.date_range("2023-06-01", "2024-01-07", periods=n)
enrollment_dates = pd.Series(enrollment_dates).sample(frac=1, random_state=42).reset_index(drop=True)

# Skewed right numeric features (need log transform)
days_since_last_visit = np.random.exponential(scale=45, size=n).clip(1, 730)
# Some missing
days_since_last_visit[np.random.choice(n, size=150, replace=False)] = np.nan

medication_cost_usd = np.random.lognormal(mean=4.2, sigma=1.1, size=n)
medication_cost_usd[np.random.choice(n, size=80, replace=False)] = np.nan

app_sessions_30d = np.random.negative_binomial(n=2, p=0.3, size=n).astype(float)
app_sessions_30d[np.random.choice(n, size=60, replace=False)] = np.nan

# Normal numeric features
age = np.random.normal(loc=58, scale=12, size=n).clip(18, 95)
age[np.random.choice(n, size=40, replace=False)] = np.nan

comorbidity_score = np.random.randint(0, 8, size=n).astype(float)
comorbidity_score[np.random.choice(n, size=30, replace=False)] = np.nan

# Categorical features
conditions = ["Type2Diabetes", "Hypertension", "COPD", "HeartFailure", "Asthma",
              "CKD", "Hyperlipidemia", "Depression", "Osteoporosis", "AFib"]
primary_condition = np.random.choice(conditions, size=n, replace=True)

insurance_type = np.random.choice(["Medicare", "Medicaid", "Commercial", "Self-Pay", "VA"],
                                   size=n, p=[0.35, 0.20, 0.30, 0.10, 0.05])
# Some missing
insurance_missing_idx = np.random.choice(n, size=100, replace=False)
insurance_type = insurance_type.astype(object)
insurance_type[insurance_missing_idx] = np.nan

# High-cardinality: pharmacy_id (200 unique pharmacies → >50 levels)
pharmacy_ids = [f"PHARM_{i:04d}" for i in range(200)]
pharmacy_id = np.random.choice(pharmacy_ids, size=n)

# Target: 30-day re-engagement (imbalanced: ~22% positive)
log_app = np.log1p(app_sessions_30d)
log_cost = np.log1p(medication_cost_usd)
logit = (
    -2.5
    + 0.03 * (age - 58) * -1
    + 0.12 * comorbidity_score
    + 0.15 * np.nan_to_num(log_app, nan=0)
    - 0.008 * np.nan_to_num(days_since_last_visit, nan=45)
    + np.random.normal(0, 0.5, size=n)
)
prob = 1 / (1 + np.exp(-logit))
target = (np.random.uniform(size=n) < prob).astype(int)

df = pd.DataFrame({
    "patient_id": [f"PT{i:06d}" for i in range(n)],
    "enrollment_date": enrollment_dates,
    "age": age,
    "comorbidity_score": comorbidity_score,
    "days_since_last_visit": days_since_last_visit,
    "medication_cost_usd": medication_cost_usd,
    "app_sessions_30d": app_sessions_30d,
    "primary_condition": primary_condition,
    "insurance_type": insurance_type,
    "pharmacy_id": pharmacy_id,
    "re_engaged_30d": target,
})

df.to_csv(WORKSPACE / "data/raw/patient_cohort.csv", index=False)

# ── Write experiment config specifying required analysis parameters ─────────────
analysis_config = {
    "n_secondary_metrics": 2,
    "base_alpha": 0.05,
    "required_power": 0.80,
    "srm_threshold": 0.01,
    "note": "Apply multiple-testing correction across primary + secondary metrics. Flag any segment with sample ratio mismatch exceeding threshold."
}
with open(WORKSPACE / "configs/analysis_config.json", "w") as f:
    json.dump(analysis_config, f, indent=2)

# ── Write modeling requirements ────────────────────────────────────────────────
modeling_spec = {
    "target_column": "re_engaged_30d",
    "date_column": "enrollment_date",
    "id_column": "patient_id",
    "drop_columns": ["patient_id", "pharmacy_id"],
    "numeric_features": ["age", "comorbidity_score", "days_since_last_visit",
                         "medication_cost_usd", "app_sessions_30d"],
    "categorical_features": ["primary_condition", "insurance_type"],
    "cv_folds": 5,
    "overfit_gap_threshold": 0.05,
    "note": "pharmacy_id is high-cardinality (200 levels) — drop it per spec. Extract cyclical time features from enrollment_date before pipeline. Use stratified cross-validation. Report both AUC-ROC and AUC-PR."
}
with open(WORKSPACE / "configs/modeling_spec.json", "w") as f:
    json.dump(modeling_spec, f, indent=2)

print("Workspace generation complete.")
print(f"Files created under {WORKSPACE}")