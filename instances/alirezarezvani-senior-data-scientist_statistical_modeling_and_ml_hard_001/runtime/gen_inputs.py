import os
import json
import random
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

WORKSPACE = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "data/raw/experiment",
    "data/raw/users",
    "data/processed",
    "data/archive/q1",
    "data/archive/q2",
    "reports/draft",
    "reports/final",
    "models/baselines",
    "models/candidates",
    "config",
    "logs",
    "notebooks",
    "sql/queries",
    "sql/migrations",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "config/db_config.yaml": "host: prod-db.internal\nport: 5432\ndb: telehealth\n",
    "config/feature_flags.json": json.dumps({"new_pricing": True, "dark_mode": False}),
    "logs/pipeline_2024_01.log": "INFO  2024-01-15 pipeline started\nERROR 2024-01-15 connection timeout\nINFO  2024-01-15 retry successful\n",
    "logs/pipeline_2024_02.log": "INFO  2024-02-01 pipeline started\nINFO  2024-02-01 completed 142000 rows\n",
    "notebooks/eda_scratch.py": "# scratch EDA\nimport pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df.describe())\n",
    "reports/draft/q1_summary.txt": "Q1 Summary: Conversion rate stable at ~10%. No significant product changes.\n",
    "reports/draft/methodology_notes.txt": "Note: always apply multiple-testing correction when using >1 metric.\n",
    "sql/queries/user_segments.sql": "SELECT user_id, plan_type, signup_date FROM users WHERE active=1;\n",
    "sql/migrations/add_session_col.sql": "ALTER TABLE events ADD COLUMN session_duration INTEGER DEFAULT NULL;\n",
    "data/archive/q1/old_experiment_results.csv": "metric,value\nconversion_rate,0.097\np_value,0.12\n",
    "data/archive/q2/deprecated_model_scores.csv": "user_id,score\n1001,0.73\n1002,0.41\n",
    "models/baselines/dummy_auc.txt": "DummyClassifier ROC-AUC: 0.500\n",
    "models/candidates/xgb_v0_params.json": json.dumps({"n_estimators": 100, "max_depth": 4}),
}
for rel_path, content in distractors.items():
    p = WORKSPACE / rel_path
    p.write_text(content)

# ── TASK INPUT 1: A/B experiment data (multi-metric) ─────────────────────────
# 3 metrics tested simultaneously → Bonferroni correction required
# Intentional SRM planted (control vs treatment ratio off)
experiment_data = {
    "experiment_name": "Q2_PricingTest_Premium_v2",
    "start_date": "2024-04-01",
    "end_date": "2024-04-28",
    "n_metrics": 3,
    "metrics": [
        {
            "name": "subscription_conversion",
            "control":   {"conversions": 1423, "visitors": 14200},
            "treatment": {"conversions": 1612, "visitors": 14350},
        },
        {
            "name": "7day_retention",
            "control":   {"conversions": 8900, "visitors": 14200},
            "treatment": {"conversions": 9180, "visitors": 14350},
        },
        {
            "name": "support_ticket_rate",
            "control":   {"conversions": 710,  "visitors": 14200},
            "treatment": {"conversions": 650,  "visitors": 14350},
        },
    ],
    "expected_split": 0.5,
}
with open(WORKSPACE / "data/raw/experiment/ab_experiment_q2.json", "w") as f:
    json.dump(experiment_data, f, indent=2)

# ── TASK INPUT 2: Messy user activity dataset for churn model ─────────────────
n_users = 3000
dates = pd.date_range("2024-01-01", periods=n_users, freq="1h")

df = pd.DataFrame({
    "user_id": np.arange(1001, 1001 + n_users),
    "signup_date": dates.strftime("%Y-%m-%d %H:%M:%S"),
    # numeric features with missing values and right skew
    "session_count_30d": np.where(
        np.random.rand(n_users) < 0.08,
        np.nan,
        np.random.negative_binomial(5, 0.3, n_users).astype(float)
    ),
    "total_spend_usd": np.where(
        np.random.rand(n_users) < 0.05,
        np.nan,
        np.random.exponential(scale=120, size=n_users)
    ),
    "avg_session_duration_min": np.where(
        np.random.rand(n_users) < 0.06,
        np.nan,
        np.abs(np.random.normal(22, 15, n_users))
    ),
    "days_since_last_login": np.where(
        np.random.rand(n_users) < 0.04,
        np.nan,
        np.random.exponential(scale=18, size=n_users)
    ),
    # categorical features
    "plan_type": np.random.choice(
        ["free", "basic", "premium", "enterprise"],
        n_users, p=[0.45, 0.30, 0.18, 0.07]
    ),
    "acquisition_channel": np.random.choice(
        ["organic", "paid_search", "referral", "social", "email", "direct"],
        n_users
    ),
    "device_type": np.random.choice(
        ["mobile", "desktop", "tablet"],
        n_users, p=[0.55, 0.35, 0.10]
    ),
    # target: churned within 60 days (imbalanced ~18%)
    "churned": np.where(
        np.random.rand(n_users) < 0.18, 1, 0
    ),
})

# Inject some obvious dirty data
df.loc[0:4, "session_count_30d"] = -999   # sentinel bad values
df.loc[5:7, "total_spend_usd"] = -1       # negative spend
df.loc[8, "plan_type"] = "PREMIUM"        # case inconsistency
df.loc[9, "acquisition_channel"] = ""     # empty string

df.to_csv(WORKSPACE / "data/raw/users/user_activity_messy.csv", index=False)

# ── TASK INPUT 3: A small metadata file describing feature roles ──────────────
feature_meta = {
    "numeric_cols": ["session_count_30d", "total_spend_usd", "avg_session_duration_min", "days_since_last_login"],
    "categorical_cols": ["plan_type", "acquisition_channel", "device_type"],
    "date_col": "signup_date",
    "target_col": "churned",
    "note": "Clean sentinel values (-999, negatives) before pipeline. Lowercase categoricals."
}
with open(WORKSPACE / "data/raw/users/feature_metadata.json", "w") as f:
    json.dump(feature_meta, f, indent=2)

print("Input generation complete.")
print(f"  experiment file : data/raw/experiment/ab_experiment_q2.json")
print(f"  user activity   : data/raw/users/user_activity_messy.csv")
print(f"  feature metadata: data/raw/users/feature_metadata.json")