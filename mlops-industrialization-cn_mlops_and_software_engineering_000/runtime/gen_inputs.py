import os
import random
import json
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── scripts/ directory with the package generator (already exists per SKILL.md) ──
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

create_package_sh = scripts_dir / "create-package.sh"
create_package_sh.write_text(textwrap.dedent("""\
    #!/usr/bin/env bash
    set -e
    PACKAGE_NAME="$1"
    if [ -z "$PACKAGE_NAME" ]; then
        echo "Usage: $0 <package_name>"
        exit 1
    fi
    BASE="src/$PACKAGE_NAME"
    mkdir -p "$BASE/io"
    mkdir -p "$BASE/domain"
    mkdir -p "$BASE/application"
    touch "$BASE/__init__.py"
    touch "$BASE/io/__init__.py"
    touch "$BASE/domain/__init__.py"
    touch "$BASE/application/__init__.py"
    echo "# I/O operations: load data, save models" > "$BASE/io/data.py"
    echo "# Domain logic: pure feature transformations" > "$BASE/domain/features.py"
    echo "# Application: orchestration of domain and io" > "$BASE/application/train.py"
    echo "Package '$PACKAGE_NAME' created at $BASE"
"""))

# ── Messy notebook prototype (distractor) ──
notebooks_dir = workspace / "notebooks"
notebooks_dir.mkdir(exist_ok=True)

nb_content = {
    "cells": [
        {"cell_type": "code", "source": ["import pandas as pd\n", "df = pd.read_csv('churn.csv')\n"]},
        {"cell_type": "code", "source": ["df['tenure_scaled'] = df['tenure'] / 72.0\n", "df['monthly_ratio'] = df['MonthlyCharges'] / df['TotalCharges'].replace(0, 1)\n"]},
        {"cell_type": "code", "source": ["from sklearn.linear_model import LogisticRegression\n", "model = LogisticRegression()\n", "model.fit(X_train, y_train)\n"]},
        {"cell_type": "code", "source": ["import pickle\n", "with open('model.pkl','wb') as f:\n", "    pickle.dump(model, f)\n"]},
    ],
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
    "nbformat": 4,
    "nbformat_minor": 5
}
(notebooks_dir / "churn_prototype.ipynb").write_text(json.dumps(nb_content, indent=2))

# ── Messy data directory (distractors) ──
data_dir = workspace / "data" / "raw"
data_dir.mkdir(parents=True, exist_ok=True)
(data_dir / "churn.csv").write_text("customerID,tenure,MonthlyCharges,TotalCharges,Churn\n7590-VHVEG,1,29.85,29.85,No\n5575-GNVDE,34,56.95,1889.5,No\n3668-QPYBK,2,53.85,108.15,Yes\n")
(data_dir / "schema.json").write_text(json.dumps({"features": ["tenure", "MonthlyCharges", "TotalCharges"], "target": "Churn"}))

# ── Old flat-layout attempt (messy / wrong structure — distractor) ──
old_pkg = workspace / "churn_pkg_old"
old_pkg.mkdir(exist_ok=True)
(old_pkg / "model.py").write_text("# old flat layout - do not use\n")
(old_pkg / "utils.py").write_text("# random utilities\n")
(old_pkg / "train.py").write_text("# deprecated training script\n")
(old_pkg / "setup.py").write_text(textwrap.dedent("""\
    from setuptools import setup
    setup(name='churn_pkg_old', version='0.1')
"""))

# ── experiments / mlruns distractors ──
experiments_dir = workspace / "experiments"
experiments_dir.mkdir(exist_ok=True)
for i in range(3):
    run_dir = experiments_dir / f"run_{i:03d}"
    run_dir.mkdir(exist_ok=True)
    (run_dir / "metrics.json").write_text(json.dumps({"accuracy": round(random.uniform(0.75, 0.92), 4), "auc": round(random.uniform(0.80, 0.95), 4)}))
    (run_dir / "params.yaml").write_text(f"C: {round(random.uniform(0.01, 10.0), 3)}\nmax_iter: {random.choice([100, 200, 500])}\n")

# ── configs (distractors) ──
configs_dir = workspace / "configs"
configs_dir.mkdir(exist_ok=True)
(configs_dir / "training_config.yaml").write_text(textwrap.dedent("""\
    model:
      type: logistic_regression
      C: 1.0
    data:
      path: data/raw/churn.csv
      test_size: 0.2
    output:
      model_path: models/churn_model.pkl
"""))
(configs_dir / "feature_config.yaml").write_text(textwrap.dedent("""\
    features:
      - tenure_scaled
      - monthly_ratio
    target: Churn
"""))

# ── Skeleton pyproject.toml — INCOMPLETE, missing [project.scripts] ──
(workspace / "pyproject.toml").write_text(textwrap.dedent("""\
    [build-system]
    requires = ["setuptools>=64", "wheel"]
    build-backend = "setuptools.backends.legacy:build"

    [project]
    name = "churn_predictor"
    version = "0.1.0"
    description = "Telecom churn prediction package"
    requires-python = ">=3.9"
    dependencies = [
        "pandas>=1.5",
        "scikit-learn>=1.2",
    ]
"""))

# ── CI / misc distractors ──
ci_dir = workspace / ".github" / "workflows"
ci_dir.mkdir(parents=True, exist_ok=True)
(ci_dir / "train.yml").write_text(textwrap.dedent("""\
    name: Train
    on: [push]
    jobs:
      train:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - run: pip install -e .
          - run: train
"""))

models_dir = workspace / "models"
models_dir.mkdir(exist_ok=True)
(models_dir / ".gitkeep").write_text("")

tests_dir = workspace / "tests"
tests_dir.mkdir(exist_ok=True)
(tests_dir / "test_features.py").write_text(textwrap.dedent("""\
    # placeholder tests
    def test_tenure_scaling():
        assert 1 / 72.0 == pytest.approx(0.01389, rel=1e-3)
"""))

# ── requirements.txt (distractor) ──
(workspace / "requirements.txt").write_text(textwrap.dedent("""\
    pandas>=1.5
    scikit-learn>=1.2
    numpy>=1.23
"""))

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")