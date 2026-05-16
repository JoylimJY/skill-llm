import os
import csv
import json
import random
import numpy as np
from pathlib import Path

random.seed(42)
np.random.seed(42)

workspace = Path("/workspace")

# ── Directory skeleton (distractor files) ──────────────────────────────────
dirs = [
    "data/raw",
    "data/processed",
    "data/archive",
    "strategies/gap_reversal",
    "strategies/momentum",
    "strategies/mean_reversion",
    "references",
    "reports/drafts",
    "reports/final",
    "scripts/utils",
    "scripts/loaders",
    "config",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ────────────────────────────────────────────────────────
(workspace / "config/db_config.yaml").write_text(
    "host: localhost\nport: 5432\ndbname: strategies\n"
)
(workspace / "config/broker_fees.json").write_text(
    json.dumps({"commission_per_share": 0.005, "min_commission": 1.0})
)
(workspace / "scripts/utils/data_cleaner.py").write_text(
    "# Utility: clean raw price feeds\ndef clean(df): return df.dropna()\n"
)
(workspace / "scripts/loaders/csv_loader.py").write_text(
    "import pandas as pd\ndef load(path): return pd.read_csv(path)\n"
)
(workspace / "strategies/momentum/idea.txt").write_text(
    "Idea: Buy stocks with 20-day momentum > 5%.\nStatus: hypothesis stage.\n"
)
(workspace / "strategies/mean_reversion/notes.md").write_text(
    "# Mean Reversion Notes\nTested 2019–2022. Marginal results.\n"
)
(workspace / "data/archive/old_signals_2018.csv").write_text(
    "date,ticker,signal\n2018-01-03,AAPL,BUY\n2018-01-04,MSFT,SELL\n"
)
(workspace / "data/archive/legacy_params.json").write_text(
    json.dumps({"stop_loss_pct": 2.5, "profit_target_pct": 5.0, "note": "deprecated"})
)
(workspace / "reports/drafts/preliminary_stats.txt").write_text(
    "Win rate rough estimate: ~55%\nNote: not final, ignore sample size concerns for now.\n"
)
(workspace / "references/market_regime_notes.txt").write_text(
    "2017-2019: bull market\n2020: crash+recovery\n2021: meme stock era\n2022: bear market\n2023: recovery\n"
)
(workspace / "scripts/utils/perf_metrics.py").write_text(
    "# Stub: compute Sharpe, drawdown etc.\npass\n"
)

# ── CORE INPUT 1: Raw trade log (messy) ─────────────────────────────────────
# Strategy: Gap-up reversal on earnings
# Baseline stop_loss=2.0%, profit_target=4.0%
# Dates span 2018-2023 (6 years, multiple regimes)

def simulate_trades(n, win_rate, avg_win_pct, avg_loss_pct, seed_offset=0):
    rng = np.random.RandomState(42 + seed_offset)
    trades = []
    start_date = np.datetime64("2018-01-15")
    for i in range(n):
        days_offset = int(rng.uniform(0, 365 * 6))
        trade_date = start_date + np.timedelta64(days_offset, "D")
        is_win = rng.rand() < win_rate
        # Add some noise
        pnl_pct = (rng.normal(avg_win_pct, 0.5) if is_win
                   else rng.normal(-avg_loss_pct, 0.3))
        ticker = rng.choice(["AAPL","MSFT","GOOG","AMZN","META","NVDA",
                               "TSLA","JPM","BAC","XOM","GS","NFLX"])
        entry_price = round(rng.uniform(50, 500), 2)
        shares = int(rng.uniform(50, 300))
        pnl_dollar = round(entry_price * shares * pnl_pct / 100, 2)
        # deliberately messy: some rows have extra whitespace, mixed case columns, N/A fields
        trades.append({
            "Trade_ID": f"T{1000+i}",
            "Date ": str(trade_date),          # trailing space in header
            "Ticker": ticker,
            "entry_price": entry_price,
            "shares": shares,
            "pnl_pct": round(pnl_pct, 4),
            "pnl_dollar": pnl_dollar,
            "stop_loss_pct": 2.0,
            "profit_target_pct": 4.0,
            "notes": rng.choice(["", "partial fill", "N/A", "slippage adj", ""]),
        })
    return trades

# 143 trades — above 100 "preferred" but below 200 "high confidence"
all_trades = simulate_trades(143, win_rate=0.54, avg_win_pct=3.8, avg_loss_pct=1.9)

# Inject a handful of obviously bad rows (missing pnl, wrong types)
all_trades[7]["pnl_pct"] = "ERROR"
all_trades[22]["pnl_dollar"] = None
all_trades[55]["Date "] = "N/A"
all_trades[99]["shares"] = ""

trade_log_path = workspace / "data/raw/gap_reversal_trades_raw.csv"
with open(trade_log_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=all_trades[0].keys())
    writer.writeheader()
    writer.writerows(all_trades)

# ── CORE INPUT 2: Parameter sweep results ──────────────────────────────────
# stop_loss sweep at 50%, 75%, 100%, 125%, 150% of baseline 2.0%
# profit_target sweep at 80%, 90%, 100%, 110%, 120% of baseline 4.0%
# For each combo: net_pnl, win_rate, num_trades (kept constant), sharpe-like ratio
# Design: stop_loss shows a PLATEAU (robust), profit_target shows a SPIKE (fragile)

baseline_sl = 2.0
baseline_pt = 4.0

sl_multipliers = [0.50, 0.75, 1.00, 1.25, 1.50]
pt_multipliers = [0.80, 0.90, 1.00, 1.10, 1.20]

# Stop-loss sensitivity: stable (plateau) around 1.0–2.5% → all multipliers profitable
sl_net_pnl = {
    0.50: 4200,   # sl=1.0% : still profitable
    0.75: 5800,   # sl=1.5% : profitable
    1.00: 6500,   # sl=2.0% : best (baseline)
    1.25: 6100,   # sl=2.5% : profitable
    1.50: 5400,   # sl=3.0% : profitable
}
sl_winrate = {0.50: 0.61, 0.75: 0.57, 1.00: 0.54, 1.25: 0.53, 1.50: 0.51}

# Profit-target sensitivity: SPIKE — only profitable near baseline 4.0%
pt_net_pnl = {
    0.80: -1200,  # pt=3.2% : loss
    0.90: 1100,   # pt=3.6% : marginally profitable
    1.00: 6500,   # pt=4.0% : great (baseline, spike)
    1.10: 800,    # pt=4.4% : barely profitable
    1.20: -2300,  # pt=4.8% : loss
}
pt_winrate = {0.80: 0.62, 0.90: 0.57, 1.00: 0.54, 1.10: 0.50, 1.20: 0.46}

sweep_rows = []
for sl_mult in sl_multipliers:
    for pt_mult in pt_multipliers:
        sl_val = round(baseline_sl * sl_mult, 3)
        pt_val = round(baseline_pt * pt_mult, 3)
        # net pnl: combine both sensitivities (use harmonic-mean-like blend)
        net = round((sl_net_pnl[sl_mult] + pt_net_pnl[pt_mult]) / 2 +
                    np.random.RandomState(int(sl_mult*100+pt_mult*100)).randint(-200,200), 2)
        wr = round((sl_winrate[sl_mult] + pt_winrate[pt_mult]) / 2, 4)
        sweep_rows.append({
            "sl_multiplier": sl_mult,
            "pt_multiplier": pt_mult,
            "stop_loss_pct": sl_val,
            "profit_target_pct": pt_val,
            "net_pnl_usd": net,
            "win_rate": wr,
            "num_trades": 143,
        })

sweep_path = workspace / "data/raw/parameter_sweep_results.csv"
with open(sweep_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=sweep_rows[0].keys())
    writer.writeheader()
    writer.writerows(sweep_rows)

# ── CORE INPUT 3: Walk-forward / OOS data ──────────────────────────────────
# In-sample: 2018-2020 (years 1-3), Out-of-sample: 2021-2023 (years 4-6)
# Deliberately: OOS sharpe is 38% of in-sample → below 50% threshold → warning

wf_data = {
    "strategy": "gap_reversal_v1",
    "in_sample_period": "2018-2020",
    "out_of_sample_period": "2021-2023",
    "in_sample_net_pnl": 5800.0,
    "out_of_sample_net_pnl": 2100.0,    # 36% of IS → below 50%
    "in_sample_sharpe": 1.42,
    "out_of_sample_sharpe": 0.54,        # 38% of IS Sharpe → below 50%
    "in_sample_win_rate": 0.58,
    "out_of_sample_win_rate": 0.49,
    "notes": "Walk forward completed Q4 2023. OOS period includes 2022 bear market.",
    "parameter_reoptimization_needed": True,   # red flag
}

wf_path = workspace / "data/processed/walkforward_summary.json"
with open(wf_path, "w") as f:
    json.dump(wf_data, f, indent=2)

# ── CORE INPUT 4: Year-by-year breakdown ───────────────────────────────────
yearly = [
    {"year": 2018, "net_pnl": 1200, "num_trades": 22, "win_rate": 0.59},
    {"year": 2019, "net_pnl": 1900, "win_rate": 0.61, "num_trades": 25},
    {"year": 2020, "net_pnl": -400, "win_rate": 0.44, "num_trades": 19},  # losing year
    {"year": 2021, "net_pnl": 2800, "win_rate": 0.57, "num_trades": 28},
    {"year": 2022, "net_pnl": -850, "win_rate": 0.41, "num_trades": 23},  # losing year
    {"year": 2023, "net_pnl": 1450, "win_rate": 0.55, "num_trades": 26},
]

yearly_path = workspace / "data/processed/yearly_breakdown.json"
with open(yearly_path, "w") as f:
    json.dump(yearly, f, indent=2)

# ── Strategy metadata ───────────────────────────────────────────────────────
meta = {
    "strategy_name": "gap_reversal_v1",
    "hypothesis": "Stocks that gap up >3% on earnings and pull back to prior day close within the first hour offer a mean-reversion entry.",
    "baseline_stop_loss_pct": 2.0,
    "baseline_profit_target_pct": 4.0,
    "asset_class": "US Equities",
    "test_period": "2018-01-01 to 2023-12-31",
    "slippage_model": "conservative_1x",   # note: only 1x, not 1.5-2x
    "commission_usd_per_share": 0.004,
}

(workspace / "strategies/gap_reversal/strategy_meta.json").write_text(
    json.dumps(meta, indent=2)
)

# ── Stub output location hint (just the directory, no file) ─────────────────
(workspace / "reports/final/.gitkeep").write_text("")

print("Workspace generated successfully.")
print(f"  Trade log:        {trade_log_path}")
print(f"  Parameter sweep:  {sweep_path}")
print(f"  Walk-forward:     {wf_path}")
print(f"  Yearly breakdown: {yearly_path}")