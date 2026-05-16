import os
import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

base = "/workspace"

# --- Create realistic directory structure with distractor files ---
dirs = [
    "data/raw",
    "data/processed",
    "data/archive",
    "models/checkpoints",
    "models/baseline",
    "reports/monthly",
    "reports/quarterly",
    "src/utils",
    "src/features",
    "config",
    "notebooks",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "config/model_config.yaml": "model_type: logistic_regression\nmax_iter: 1000\nC: 0.5\n",
    "config/data_config.yaml": "train_size: 0.8\nrandom_state: 99\ntarget_col: is_default\n",
    "src/utils/logger.py": "import logging\ndef get_logger(name):\n    return logging.getLogger(name)\n",
    "src/utils/helpers.py": "def flatten(lst):\n    return [x for sublist in lst for x in sublist]\n",
    "src/features/encoding.py": "# placeholder for encoding utilities\ndef label_encode(series):\n    return series.astype('category').cat.codes\n",
    "models/baseline/baseline_auc.txt": "Baseline logistic regression AUC: 0.612\n",
    "models/checkpoints/checkpoint_v1.txt": "Epoch 1: loss=0.45\nEpoch 2: loss=0.38\n",
    "reports/monthly/april_summary.txt": "Total applications: 12400\nApproval rate: 68%\nDefault rate: 4.2%\n",
    "reports/quarterly/q1_2024.txt": "Net credit loss: 1.8M\nProvision coverage: 112%\n",
    "notebooks/eda_draft.py": "# Exploratory analysis - draft\nimport pandas as pd\ndf = pd.read_csv('../data/raw/loans.csv')\nprint(df.describe())\n",
    "logs/training_run_20240315.log": "[INFO] Data loaded: 15000 rows\n[INFO] Model training started\n[ERROR] NaN detected in feature age\n[INFO] Training complete\n",
    "data/archive/loans_2022.csv": "id,age,income,is_default\n1,25,30000,0\n2,45,55000,1\n",
}
for path, content in distractor_files.items():
    with open(os.path.join(base, path), "w") as f:
        f.write(content)

# --- Generate realistic messy loan dataset ---
n = 5000

age = np.random.normal(35, 10, n).clip(18, 75).astype(int)
income = np.random.lognormal(10.5, 0.6, n).clip(8000, 500000)
loan_amount = np.random.lognormal(9.8, 0.7, n).clip(1000, 300000)
credit_history_months = np.random.randint(0, 240, n)
num_prev_loans = np.random.poisson(2.5, n)
debt_to_income = np.random.beta(2, 5, n) * 1.5
employment_years = np.random.exponential(5, n).clip(0, 40)
num_late_payments = np.random.poisson(1.2, n)
loan_to_value = np.random.beta(3, 3, n) * 2.0
monthly_obligations = np.random.lognormal(7.5, 0.8, n).clip(500, 50000)

# Introduce NaNs (messiness)
for arr, frac in [(income, 0.03), (credit_history_months, 0.05),
                  (employment_years, 0.04), (debt_to_income, 0.02)]:
    idx = np.random.choice(n, int(n * frac), replace=False)
    arr = arr.astype(float)
    arr[idx] = np.nan
    if arr is income: income = arr
    elif arr is credit_history_months: credit_history_months = arr.astype(float)
    elif arr is employment_years: employment_years = arr
    elif arr is debt_to_income: debt_to_income = arr

# Default label: logistic function of features
log_odds = (
    -3.5
    + 0.025 * num_late_payments
    + 0.8 * debt_to_income
    - 0.003 * (np.nan_to_num(credit_history_months, nan=12))
    + 0.4 * loan_to_value
    - 0.00001 * np.nan_to_num(income, nan=30000)
    + 0.15 * np.log1p(loan_amount / np.nan_to_num(income, nan=30000) * 12)
    + 0.2 * (num_prev_loans > 3).astype(float)
)
prob_default = 1 / (1 + np.exp(-log_odds))
is_default = np.random.binomial(1, prob_default)

df = pd.DataFrame({
    "loan_id": [f"LN{str(i).zfill(5)}" for i in range(1, n+1)],
    "age": age.astype(float),
    "annual_income": income,
    "loan_amount": loan_amount,
    "credit_history_months": credit_history_months,
    "num_prev_loans": num_prev_loans.astype(float),
    "debt_to_income_ratio": debt_to_income,
    "employment_years": employment_years,
    "num_late_payments": num_late_payments.astype(float),
    "loan_to_value_ratio": loan_to_value,
    "monthly_obligations": monthly_obligations,
    "is_default": is_default,
})

# Introduce some outlier rows (messy)
outlier_idx = np.random.choice(n, 50, replace=False)
df.loc[outlier_idx, "annual_income"] = np.random.uniform(5000000, 10000000, 50)
df.loc[outlier_idx[:25], "debt_to_income_ratio"] = np.random.uniform(5, 20, 25)

df.to_csv(os.path.join(base, "data/raw/loan_applications.csv"), index=False)

print("Workspace generated successfully.")
print(f"Dataset shape: {df.shape}")
print(f"Default rate: {df['is_default'].mean():.3f}")