import os
import random
import json
import numpy as np
import pandas as pd
from pathlib import Path

random.seed(42)
np.random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "src",
    "src/utils",
    "data/raw",
    "data/processed",
    "data/reports",
    "notebooks",
    "configs",
    "tests",
    "deploy",
    "deploy/docker",
    "artifacts",
    "logs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
(WORKSPACE / "configs" / "hyperparams.yaml").write_text(
    "learning_rate: 0.01\nn_estimators: 100\nmax_depth: 5\n"
)
(WORKSPACE / "configs" / "feature_config.json").write_text(
    json.dumps({"features": ["age", "income", "balance", "num_products", "tenure"], "target": "churn"})
)
(WORKSPACE / "deploy" / "docker" / "Dockerfile.prod").write_text(
    "FROM python:3.10-slim\nCOPY . /app\nWORKDIR /app\nRUN pip install -r requirements.txt\n"
)
(WORKSPACE / "deploy" / "serve.sh").write_text(
    "#!/bin/bash\ngunicorn app:app --bind 0.0.0.0:8000\n"
)
(WORKSPACE / "logs" / "training_2024_01.log").write_text(
    "[INFO] Epoch 1/10 - loss: 0.432\n[INFO] Epoch 2/10 - loss: 0.381\n[ERROR] NaN detected in epoch 8\n"
)
(WORKSPACE / "logs" / "drift_alert_legacy.txt").write_text(
    "LEGACY: drift score exceeded threshold 0.25 on 2024-01-15\n"
)
(WORKSPACE / "notebooks" / "eda_exploration.ipynb").write_text(
    json.dumps({"nbformat": 4, "nbformat_minor": 5, "cells": [], "metadata": {}})
)
(WORKSPACE / "notebooks" / "feature_analysis.py").write_text(
    "# Exploratory analysis\nimport pandas as pd\ndf = pd.read_csv('../data/raw/train_data.csv')\nprint(df.describe())\n"
)
(WORKSPACE / "src" / "utils" / "preprocessing.py").write_text(
    "import pandas as pd\n\ndef scale_features(df):\n    return (df - df.mean()) / df.std()\n\ndef encode_categoricals(df, cols):\n    return pd.get_dummies(df, columns=cols)\n"
)
(WORKSPACE / "src" / "utils" / "metrics.py").write_text(
    "from sklearn.metrics import accuracy_score, roc_auc_score\n\ndef evaluate(y_true, y_pred):\n    return {'accuracy': accuracy_score(y_true, y_pred), 'auc': roc_auc_score(y_true, y_pred)}\n"
)
(WORKSPACE / "tests" / "test_preprocessing.py").write_text(
    "import pytest\nfrom src.utils.preprocessing import scale_features\nimport pandas as pd\nimport numpy as np\n\ndef test_scale():\n    df = pd.DataFrame({'a': [1.0,2.0,3.0]})\n    scaled = scale_features(df)\n    assert abs(scaled['a'].mean()) < 1e-9\n"
)
(WORKSPACE / "artifacts" / ".gitkeep").write_text("")
(WORKSPACE / "data" / "processed" / ".gitkeep").write_text("")
(WORKSPACE / "data" / "reports" / ".gitkeep").write_text("")

# ── Broken requirements.txt (distractor) ─────────────────────────────────────
(WORKSPACE / "requirements.txt").write_text(
    "scikit-learn\npandas\nnumpy\n# mlflow  <- commented out, not tracked yet\n# evidently <- not installed\nflask\ngunicorn\n"
)

# ── Reference training data (stable distribution) ────────────────────────────
N_TRAIN = 500
ages_train = np.random.normal(42, 12, N_TRAIN).clip(18, 80).astype(int)
incomes_train = np.random.normal(55000, 15000, N_TRAIN).clip(10000, 150000)
balances_train = np.random.normal(3500, 1200, N_TRAIN).clip(0, 12000)
products_train = np.random.choice([1, 2, 3, 4], N_TRAIN, p=[0.4, 0.35, 0.2, 0.05])
tenure_train = np.random.randint(1, 15, N_TRAIN)
churn_prob = 1 / (1 + np.exp(-((-0.03 * ages_train) + (0.00001 * incomes_train) - (0.0002 * balances_train) + (0.1 * products_train) - (0.05 * tenure_train))))
churn_train = (np.random.rand(N_TRAIN) < churn_prob).astype(int)

train_df = pd.DataFrame({
    "age": ages_train,
    "income": incomes_train.round(2),
    "balance": balances_train.round(2),
    "num_products": products_train,
    "tenure": tenure_train,
    "churn": churn_train
})
train_df.to_csv(WORKSPACE / "data" / "raw" / "train_data.csv", index=False)

# ── Production data (DRIFTED distribution) ───────────────────────────────────
N_PROD = 300
# Inject significant drift: age shifted up, income dropped, balance near-zero for many
ages_prod = np.random.normal(58, 8, N_PROD).clip(18, 80).astype(int)       # older cohort
incomes_prod = np.random.normal(32000, 8000, N_PROD).clip(10000, 150000)   # lower income
balances_prod = np.random.normal(800, 400, N_PROD).clip(0, 12000)           # much lower
products_prod = np.random.choice([1, 2, 3, 4], N_PROD, p=[0.7, 0.2, 0.08, 0.02])
tenure_prod = np.random.randint(1, 5, N_PROD)
churn_prob_p = 1 / (1 + np.exp(-((-0.03 * ages_prod) + (0.00001 * incomes_prod) - (0.0002 * balances_prod) + (0.1 * products_prod) - (0.05 * tenure_prod))))
churn_prod = (np.random.rand(N_PROD) < churn_prob_p).astype(int)

prod_df = pd.DataFrame({
    "age": ages_prod,
    "income": incomes_prod.round(2),
    "balance": balances_prod.round(2),
    "num_products": products_prod,
    "tenure": tenure_prod,
    "churn": churn_prod
})
prod_df.to_csv(WORKSPACE / "data" / "raw" / "prod_data.csv", index=False)

# ── Broken / incomplete training script (agent must fix + instrument) ─────────
broken_train_script = '''#!/usr/bin/env python3
"""
Credit Risk Churn Model - Training Script
NOTE: This script is NOT production-ready. Missing observability, reproducibility controls.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss

# TODO: seeds not set - results are non-reproducible
# TODO: no experiment tracking
# TODO: no model artifact saving

DATA_PATH = "data/raw/train_data.csv"
FEATURES = ["age", "income", "balance", "num_products", "tenure"]
TARGET = "churn"
N_ESTIMATORS = 150
MAX_DEPTH = 6
TEST_SIZE = 0.2

def load_data(path):
    df = pd.read_csv(path)
    X = df[FEATURES]
    y = df[TARGET]
    return X, y

def build_model():
    return RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        random_state=99   # <-- wrong seed, not matching policy
    )

def main():
    X, y = load_data(DATA_PATH)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE
        # missing: random_state
    )
    model = build_model()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    proba = model.predict_proba(X_test)

    acc = accuracy_score(y_test, preds)
    loss = log_loss(y_test, proba)

    print(f"Accuracy: {acc:.4f}")
    print(f"Log Loss: {loss:.4f}")
    # Results printed but never tracked anywhere

if __name__ == "__main__":
    main()
'''
(WORKSPACE / "src" / "train.py").write_text(broken_train_script)

# ── Stub for SKILL.md references directory ───────────────────────────────────
(WORKSPACE / "references").mkdir(exist_ok=True)
(WORKSPACE / "references" / "mlflow-tracking.py").write_text(
    "# Reference implementation stub - see SKILL.md for usage patterns\n"
    "# setup_tracking(), log_training_run() are illustrative function names\n"
)

print("Workspace generated successfully.")
print(f"  Train data: {N_TRAIN} rows -> data/raw/train_data.csv")
print(f"  Prod data:  {N_PROD} rows (drifted) -> data/raw/prod_data.csv")
print(f"  Broken training script: src/train.py")