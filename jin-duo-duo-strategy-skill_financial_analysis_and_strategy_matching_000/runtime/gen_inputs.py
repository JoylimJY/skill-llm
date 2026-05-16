#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate the sandbox workspace for the jin-duo-duo strategy skill evaluation.
"""

import os
import json
import random
import numpy as np
import pandas as pd
from pathlib import Path

# Fixed seed for determinism
SEED = 20240601
random.seed(SEED)
np.random.seed(SEED)

workspace = Path("/workspace")

# ─────────────────────────────────────────────
# 1. Create directory structure
# ─────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "data/raw",
    "data/processed",
    "reports/archive",
    "reports/drafts",
    "logs",
    "config",
    "tmp",
    "backups/2023",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 2. Create distractor files
# ─────────────────────────────────────────────

# Distractor: old report
(workspace / "reports/archive/stock_XYZ_2023Q4.txt").write_text(
    "Old quarterly report for XYZ. Not relevant. Strategy: Hold.\n"
)

# Distractor: config file
(workspace / "config/analysis_config.yaml").write_text(
    "strategy: auto\nthreshold: 65\noutput_format: csv\n"
)

# Distractor: log files
(workspace / "logs/run_20240101.log").write_text(
    "[INFO] Analysis started.\n[INFO] No data found.\n[ERROR] File not found: stock_data.csv\n"
)
(workspace / "logs/run_20240201.log").write_text(
    "[INFO] Analysis started.\n[WARNING] Insufficient data: 15 rows only.\n"
)

# Distractor: wrong/incomplete CSV
(workspace / "data/raw/incomplete_stock.csv").write_text(
    "date,close,volume\n2024-01-01,10.0,100000\n2024-01-02,10.1,110000\n"
)

# Distractor: unrelated JSON
(workspace / "data/raw/sector_info.json").write_text(json.dumps({
    "sector": "Technology",
    "stocks": ["XYZ", "ABC", "DEF"],
    "note": "Sector rotation expected Q2 2024"
}, ensure_ascii=False, indent=2))

# Distractor: draft report with wrong strategy
(workspace / "reports/drafts/draft_analysis.txt").write_text(
    "Draft: Stock XYZ appears bullish. Preliminary strategy: 策略一 (but not confirmed).\n"
    "Score: 45 (BELOW THRESHOLD - do not use)\n"
)

# Distractor: backup data with different stock
(workspace / "backups/2023/stock_ABC_backup.csv").write_text(
    "date,open,high,low,close,volume\n"
    "2023-06-01,20.0,20.5,19.8,20.2,500000\n"
    "2023-06-02,20.2,20.8,20.0,20.6,600000\n"
)

# Distractor: processed but stale data
(workspace / "data/processed/XYZ_indicators_OLD.json").write_text(json.dumps({
    "status": "stale",
    "data_count": 30,
    "note": "Generated 2023-12-01. Do not use for current analysis."
}, ensure_ascii=False, indent=2))

# Distractor: README-like file about the project (not the skill)
(workspace / "config/project_notes.txt").write_text(
    "Project: JinDuoDuo Strategy System v2\n"
    "Owner: Quant Team\n"
    "Status: Active\n"
    "Note: Always use latest data. Minimum 60 trading days recommended.\n"
)

# Distractor: tmp scratch
(workspace / "tmp/scratch.txt").write_text(
    "Testing MA calculation manually:\nMA5 on last 5 days ~ 11.2\nNot reliable, use the script.\n"
)

# ─────────────────────────────────────────────
# 3. Generate the engineered stock CSV
#    Design goal:
#    - 80 trading days
#    - Phase 1 (days 1-40): gradual uptrend → forms new high
#    - Phase 2 (days 41-80): price pulls back, touches MA20, volume shrinks
#      BUT MACD shows top divergence + death cross during pullback
#    → Strategy 2 (回踩买入) score ≥ 60 [triggered]
#    → Strategy 4 (减仓信号) score ≥ 50 [triggered]
#    → Priority rule: sell > buy → Strategy 4 WINS
# ─────────────────────────────────────────────

n_days = 80
dates = pd.bdate_range(start="2024-01-02", periods=n_days)

# Build price series
close = np.zeros(n_days)
open_ = np.zeros(n_days)
high = np.zeros(n_days)
low = np.zeros(n_days)
volume = np.zeros(n_days, dtype=np.int64)

# Phase 1: Uptrend (days 0-39): price climbs from ~10.0 to ~14.5
for i in range(40):
    if i == 0:
        close[i] = 10.0
    else:
        daily_change = np.random.uniform(0.05, 0.25)  # mostly up
        close[i] = close[i-1] + daily_change
    noise_o = np.random.uniform(-0.1, 0.1)
    noise_h = np.random.uniform(0.05, 0.35)
    noise_l = np.random.uniform(-0.35, -0.05)
    open_[i] = close[i] + noise_o
    high[i] = max(close[i], open_[i]) + noise_h
    low[i] = min(close[i], open_[i]) + noise_l
    volume[i] = int(np.random.uniform(1_200_000, 2_000_000))

# Price peak at day 39 ≈ 14.5
peak_price = close[39]

# Phase 2: Pullback (days 40-79)
# Price pulls back toward MA20, which will be around 12.8-13.0
# MACD should show top divergence: price makes a small new high early in phase 2
# then falls; MACD at that small new high is lower than at the original peak

# Days 40-44: small bounce to create "new high" for MACD divergence
for i in range(40, 45):
    if i == 40:
        close[i] = close[i-1] + np.random.uniform(0.1, 0.3)  # slight new high
    else:
        close[i] = close[i-1] + np.random.uniform(-0.05, 0.15)
    open_[i] = close[i] + np.random.uniform(-0.1, 0.1)
    high[i] = max(close[i], open_[i]) + np.random.uniform(0.05, 0.25)
    low[i] = min(close[i], open_[i]) + np.random.uniform(-0.2, -0.05)
    volume[i] = int(np.random.uniform(800_000, 1_200_000))  # volume diminishing at new high

# Days 45-65: decline toward MA20
for i in range(45, 66):
    decline = np.random.uniform(0.08, 0.22)
    close[i] = close[i-1] - decline
    open_[i] = close[i] + np.random.uniform(-0.1, 0.2)
    high[i] = max(close[i], open_[i]) + np.random.uniform(0.02, 0.18)
    low[i] = min(close[i], open_[i]) + np.random.uniform(-0.25, -0.05)
    volume[i] = int(np.random.uniform(600_000, 900_000))  # shrinking volume

# Days 66-75: consolidate near MA20 area — create 金针探底 at day 70
for i in range(66, 76):
    if i == 70:  # 金针探底 candle
        close[i] = close[i-1] + np.random.uniform(0.0, 0.1)
        open_[i] = close[i] + np.random.uniform(-0.05, 0.05)
        high[i] = max(close[i], open_[i]) + np.random.uniform(0.05, 0.15)
        low[i] = min(close[i], open_[i]) - np.random.uniform(0.5, 0.8)  # long lower shadow
    else:
        delta = np.random.uniform(-0.1, 0.1)
        close[i] = close[i-1] + delta
        open_[i] = close[i] + np.random.uniform(-0.08, 0.08)
        high[i] = max(close[i], open_[i]) + np.random.uniform(0.03, 0.15)
        low[i] = min(close[i], open_[i]) + np.random.uniform(-0.2, -0.03)
    volume[i] = int(np.random.uniform(500_000, 750_000))  # low volume, 缩量

# Days 76-79: slight recovery but volume still low
for i in range(76, 80):
    close[i] = close[i-1] + np.random.uniform(-0.05, 0.1)
    open_[i] = close[i] + np.random.uniform(-0.05, 0.05)
    high[i] = max(close[i], open_[i]) + np.random.uniform(0.03, 0.12)
    low[i] = min(close[i], open_[i]) + np.random.uniform(-0.12, -0.03)
    volume[i] = int(np.random.uniform(480_000, 680_000))

# ─── Adjust to ensure MA20 is correctly touched ───
# Compute MA20 at day 79 using numpy rolling
close_series = pd.Series(close)
ma20_series = close_series.rolling(20).mean()
ma20_at_end = ma20_series.iloc[-1]
ma5_at_end = close_series.rolling(5).mean().iloc[-1]

# We want close[-1] to be within 1.5% of MA20 (回踩 MA20)
# Shift the last 10 days slightly to make close approach ma20
current_last = close[-1]
target_last = ma20_at_end * np.random.uniform(0.99, 1.015)
adjustment = target_last - current_last
# Apply gradually
for i in range(70, 80):
    close[i] += adjustment * (i - 69) / 10
    open_[i] += adjustment * (i - 69) / 10
    high[i] += adjustment * (i - 69) / 10
    low[i] += adjustment * (i - 69) / 10

# Recompute MA20 and verify
close_series = pd.Series(close)
ma20_final = close_series.rolling(20).mean().iloc[-1]
ma5_final = close_series.rolling(5).mean().iloc[-1]
ma10_final = close_series.rolling(10).mean().iloc[-1]
ma60_final = close_series.rolling(60).mean().iloc[-1] if len(close_series) >= 60 else None

# ─── Build DataFrame ───
df = pd.DataFrame({
    'date': dates.strftime('%Y-%m-%d'),
    'open': np.round(open_, 2),
    'high': np.round(high, 2),
    'low': np.round(low, 2),
    'close': np.round(close, 2),
    'volume': volume.astype(int)
})

# Ensure high >= open, close and low <= open, close
df['high'] = df[['high', 'open', 'close']].max(axis=1).round(2)
df['low'] = df[['low', 'open', 'close']].min(axis=1).round(2)

# Save CSV
csv_path = workspace / "data" / "raw" / "XYZ_stock_history.csv"
df.to_csv(csv_path, index=False)

print(f"[gen_inputs] Created stock CSV: {csv_path} ({n_days} rows)")
print(f"[gen_inputs] Close price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
print(f"[gen_inputs] Last close: {df['close'].iloc[-1]:.2f}")
print(f"[gen_inputs] MA20 at end: {ma20_final:.2f}")
print(f"[gen_inputs] MA5 at end: {ma5_final:.2f}")
print(f"[gen_inputs] Directory structure created with {sum(1 for _ in workspace.rglob('*') if _.is_file())} files")
print("[gen_inputs] Workspace ready for agent.")