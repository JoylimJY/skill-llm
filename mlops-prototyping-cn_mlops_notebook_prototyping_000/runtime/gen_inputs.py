import os
import json
import stat
import textwrap

WORKSPACE = "/workspace"

# ── directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "models/archived",
    "reports/q1",
    "reports/q2",
    "notebooks/drafts",
    "notebooks/archive",
    "src/features",
    "src/utils",
    "tests",
    "configs",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "data/raw/transactions_2023.csv": "id,amount,label\n1,120.5,0\n2,9999.0,1\n3,45.2,0\n",
    "data/processed/features_v2.parquet.placeholder": "# placeholder – real file generated at runtime",
    "models/archived/lgbm_v1.pkl.placeholder": "# old model – do not use",
    "reports/q1/summary.txt": "Q1 fraud rate: 2.3%\nTotal transactions: 1,200,000\n",
    "reports/q2/summary.txt": "Q2 fraud rate: 2.7%\nTotal transactions: 1,350,000\n",
    "notebooks/archive/exploratory_old.ipynb.bak": "# old notebook – superseded",
    "src/features/engineering.py": "def add_time_features(df):\n    return df\n",
    "src/utils/logger.py": "import logging\nlogger = logging.getLogger(__name__)\n",
    "tests/test_features.py": "def test_placeholder():\n    assert True\n",
    "configs/model_config.yaml": "model: logistic_regression\nthreshold: 0.5\n",
    "configs/data_config.yaml": "raw_path: data/raw/transactions_2023.csv\ntest_size: 0.2\n",
    "notebooks/drafts/scratch.py": "# scratch pad – not a notebook\nimport pandas as pd\n",
}
for rel_path, content in distractors.items():
    full = os.path.join(WORKSPACE, rel_path)
    with open(full, "w") as f:
        f.write(content)

# ── check-notebook.sh ─────────────────────────────────────────────────────────
# This is the proprietary validator the agent must satisfy.
# It checks for: H1 markdown title, ## Imports heading, ## Config heading,
# data-loading code, and sklearn Pipeline usage.
check_script = r"""#!/usr/bin/env bash
set -euo pipefail

NOTEBOOK="${1:-}"
if [[ -z "$NOTEBOOK" ]]; then
  echo "Usage: $0 <notebook.ipynb>" >&2
  exit 1
fi

if [[ ! -f "$NOTEBOOK" ]]; then
  echo "ERROR: File not found: $NOTEBOOK" >&2
  exit 2
fi

PASS=0
FAIL=0

check() {
  local name="$1"
  local pattern="$2"
  local target="$3"
  if python3 - "$NOTEBOOK" "$pattern" <<'PYEOF'
import sys, json, re
nb = json.load(open(sys.argv[1]))
pat = sys.argv[2]
for cell in nb.get("cells", []):
    src = "".join(cell.get("source", []))
    if re.search(pat, src):
        sys.exit(0)
sys.exit(1)
PYEOF
  then
    echo "  [PASS] $name"
    return 0
  else
    echo "  [FAIL] $name"
    return 1
  fi
}

echo "=== Notebook Structure Check: $NOTEBOOK ==="

check "H1 title"        "^#[[:space:]]+\S"                       && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "Imports section" "##[[:space:]]+Imports"                  && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "Config section"  "##[[:space:]]+Config"                   && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "Data loading"    "(read_csv|read_parquet|load_dataset|datasets\.load)" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "Pipeline usage"  "Pipeline\s*\("                          && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

echo ""
echo "Results: $PASS passed, $FAIL failed"

if [[ $FAIL -gt 0 ]]; then
  echo "STATUS: FAIL"
  exit 1
else
  echo "STATUS: PASS"
  exit 0
fi
"""

script_path = os.path.join(WORKSPACE, "scripts", "check-notebook.sh")
with open(script_path, "w") as f:
    f.write(check_script)
os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── SKILL.md ──────────────────────────────────────────────────────────────────
skill_md = textwrap.dedent("""\
    ---
    name: mlops-prototyping-cn
    version: 1.0.0
    description: Structured Jupyter notebook prototyping with pipeline integrity
    license: MIT
    ---

    # MLOps Prototyping 🔬

    Create standardized, reproducible Jupyter notebooks.

    ## Features

    ### 1. Notebook Structure Check ✅

    Validate notebook follows best practices:

    ```bash
    ./scripts/check-notebook.sh notebook.ipynb
    ```

    Checks for:
    - H1 title
    - Imports section
    - Config/Constants
    - Data loading
    - Pipeline usage

    ### 2. Template 📝

    Use this structure:

    1. **Title & Purpose**
    2. **Imports** (standard → third-party → local)
    3. **Configs** (all constants at top)
    4. **Datasets** (load, validate, split)
    5. **Analysis** (EDA)
    6. **Modeling** (use `sklearn.pipeline.Pipeline`)
    7. **Evaluations** (metrics on test data)

    ## Quick Start

    ```bash
    # Check your notebook
    ./scripts/check-notebook.sh my-notebook.ipynb

    # Follow structure in notebook
    # Use Pipeline for all transforms
    # Set RANDOM_STATE everywhere
    ```

    ## Key Rules

    ✅ **DO:**
    - Put all params in Config section
    - Use `sklearn.pipeline.Pipeline`
    - Split data BEFORE any transforms
    - Set `random_state` everywhere

    ❌ **DON'T:**
    - Magic numbers in code
    - Manual transforms (use Pipeline)
    - Fit on full dataset (data leakage)

    ## Author

    Converted from [MLOps Coding Course](https://github.com/MLOps-Courses/mlops-coding-skills)

    ## Changelog

    ### v1.0.0 (2026-02-18)
    - Initial OpenClaw conversion
    - Added notebook checker
""")

with open(os.path.join(WORKSPACE, "SKILL.md"), "w") as f:
    f.write(skill_md)

# ── intentionally broken "draft" notebook (agent must NOT use this as-is) ────
# It violates every rule: no headings, magic numbers, manual transforms, leakage
bad_nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
    "cells": [
        {
            "cell_type": "code",
            "id": "aaa1",
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd\n",
                "import numpy as np\n",
                "from sklearn.preprocessing import StandardScaler\n",
                "from sklearn.linear_model import LogisticRegression\n",
            ]
        },
        {
            "cell_type": "code",
            "id": "aaa2",
            "metadata": {},
            "outputs": [],
            "source": [
                "df = pd.read_csv('data/raw/transactions_2023.csv')\n",
                "# BAD: fit scaler on full dataset before split\n",
                "scaler = StandardScaler()\n",
                "df[['amount']] = scaler.fit_transform(df[['amount']])\n",
                "X = df[['amount']]\n",
                "y = df['label']\n",
            ]
        },
        {
            "cell_type": "code",
            "id": "aaa3",
            "metadata": {},
            "outputs": [],
            "source": [
                "from sklearn.model_selection import train_test_split\n",
                "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)\n",
                "# BAD: no random_state, magic number 0.2\n",
                "model = LogisticRegression()\n",
                "model.fit(X_train, y_train)\n",
            ]
        },
    ]
}
with open(os.path.join(WORKSPACE, "notebooks", "drafts", "fraud_detection_DRAFT.ipynb"), "w") as f:
    json.dump(bad_nb, f, indent=2)

print("Workspace generated successfully.")