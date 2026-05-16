import os
import random
import numpy as np
import pandas as pd
import json

random.seed(42)
np.random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Directory structure with distractors ---
dirs = [
    "data/raw",
    "data/processed",
    "data/macro",
    "research/notes",
    "research/reports",
    "backtest/results",
    "backtest/configs",
    "scripts",
    "archive/2022",
    "archive/2023",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---

# 1. Macro data (irrelevant)
macro_data = pd.DataFrame({
    "date": ["2024-01", "2024-02", "2024-03"],
    "CPI": [2.1, 2.3, 2.0],
    "PMI": [50.2, 49.8, 50.5],
    "M2_growth": [8.5, 8.7, 8.4],
})
macro_data.to_csv(os.path.join(workspace, "data/macro/macro_indicators.csv"), index=False)

# 2. Wrong period data (1-month returns only, distractor)
one_month_stocks = [f"60{str(i).zfill(4)}.SH" for i in range(1, 21)]
one_month_df = pd.DataFrame({
    "stock_code": one_month_stocks,
    "return_2024_03": np.random.uniform(-0.15, 0.20, size=20).round(4),
})
one_month_df.to_csv(os.path.join(workspace, "data/raw/one_month_snapshot.csv"), index=False)

# 3. Archive old strategy results
old_results = {
    "strategy": "momentum_1m",
    "period": "2023Q4",
    "annualized_return": 0.12,
    "sharpe": 1.3,
    "note": "outdated, do not use"
}
with open(os.path.join(workspace, "archive/2023/old_strategy_result.json"), "w") as f:
    json.dump(old_results, f, indent=2)

# 4. Distractor config
config_distractor = {
    "observation_months": 1,
    "holding_months": 1,
    "num_groups": 3,
    "strategy": "momentum",
    "note": "1-month momentum config, not for current task"
}
with open(os.path.join(workspace, "backtest/configs/momentum_1m_config.json"), "w") as f:
    json.dump(config_distractor, f, indent=2)

# 5. Distractor processed file (arithmetic mean, wrong method)
distractor_processed = pd.DataFrame({
    "stock_code": [f"00{str(i).zfill(4)}.SZ" for i in range(1, 11)],
    "arithmetic_mean_return": np.random.uniform(-0.05, 0.10, size=10).round(4),
    "note": ["arithmetic mean, incorrect method"] * 10
})
distractor_processed.to_csv(os.path.join(workspace, "data/processed/wrong_method_returns.csv"), index=False)

# 6. Research notes (distractor text)
with open(os.path.join(workspace, "research/notes/strategy_ideas.txt"), "w") as f:
    f.write("Ideas:\n- Try 6-month momentum\n- Consider sector rotation\n- Look at volume signals\n")

# 7. Another distractor: 5-year long-term data
long_term = pd.DataFrame({
    "year": [2019, 2020, 2021, 2022, 2023],
    "market_return": [0.22, 0.18, 0.05, -0.12, 0.08],
    "strategy_return": [0.31, 0.25, 0.07, -0.09, 0.11],
})
long_term.to_csv(os.path.join(workspace, "archive/2022/long_term_backtest.csv"), index=False)

# 8. Scripts directory placeholder
with open(os.path.join(workspace, "scripts/fetch_data.py"), "w") as f:
    f.write("# Data fetching script - not needed for current analysis\nprint('data fetch stub')\n")

# 9. Distractor report template
with open(os.path.join(workspace, "research/reports/template.txt"), "w") as f:
    f.write("Strategy Report Template\n========================\nFill in: period, returns, groups\n")

# 10. Backtest results placeholder
with open(os.path.join(workspace, "backtest/results/placeholder.txt"), "w") as f:
    f.write("No results yet. Run backtest first.\n")

# --- MAIN INPUT: 3-month stock return data (messy) ---
# 50 A-share stocks with monthly returns for Jan, Feb, Mar 2024
# Messy: some values in PERCENTAGE format (e.g., "3.25%" instead of 0.0325)
# Some missing values (NaN) for a few stocks in one month
# Some stocks with clearly wrong/extreme values to test robustness

np.random.seed(42)
n_stocks = 50
stock_codes = []
for i in range(1, 31):
    stock_codes.append(f"60{str(i).zfill(4)}.SH")
for i in range(1, 21):
    stock_codes.append(f"00{str(i).zfill(4)}.SZ")

# Generate base returns: ~ normal distribution
jan_returns = np.random.normal(0.01, 0.06, n_stocks)
feb_returns = np.random.normal(0.005, 0.055, n_stocks)
mar_returns = np.random.normal(-0.005, 0.065, n_stocks)

# Introduce messiness:
# 1. Some values as percentage strings (indices 5, 12, 23, 37, 44)
# 2. Some NaN values (indices 8, 19, 31) - in different months
# 3. One clearly erroneous value that's already decimal (keep as is, within range)

jan_col = []
feb_col = []
mar_col = []

percent_indices = {5, 12, 23, 37, 44}
nan_jan = {8}
nan_feb = {19}
nan_mar = {31}

for i in range(n_stocks):
    if i in nan_jan:
        jan_col.append(None)
    elif i in percent_indices:
        jan_col.append(f"{round(jan_returns[i]*100, 2)}%")
    else:
        jan_col.append(round(jan_returns[i], 4))

    if i in nan_feb:
        feb_col.append(None)
    elif i in percent_indices:
        feb_col.append(f"{round(feb_returns[i]*100, 2)}%")
    else:
        feb_col.append(round(feb_returns[i], 4))

    if i in nan_mar:
        mar_col.append(None)
    elif i in percent_indices:
        mar_col.append(f"{round(mar_returns[i]*100, 2)}%")
    else:
        mar_col.append(round(mar_returns[i], 4))

main_df = pd.DataFrame({
    "stock_code": stock_codes,
    "return_2024_01": jan_col,
    "return_2024_02": feb_col,
    "return_2024_03": mar_col,
})

main_df.to_csv(os.path.join(workspace, "data/raw/a_share_monthly_returns.csv"), index=False)

print("Workspace generated successfully.")
print(f"Main input file: {workspace}/data/raw/a_share_monthly_returns.csv")
print(f"Total stocks: {n_stocks}")
print(f"Stocks with percentage-format values: {percent_indices}")
print(f"Stocks with NaN (jan): {nan_jan}, (feb): {nan_feb}, (mar): {nan_mar}")