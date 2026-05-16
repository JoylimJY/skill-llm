import os
import json
import csv
import random

random.seed(42)

workspace = "/workspace"

# ── Directory structure with distractors ──────────────────────────────────────
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/archive",
    "config",
    "logs",
    "reports",
    "notebooks",
    "tests",
    "docs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractors = {
    "scripts/email_reporter.py": "# email reporter stub\nprint('email reporter')\n",
    "scripts/technical_analyzer.py": "# technical analyzer stub\nprint('technical analyzer')\n",
    "scripts/valuation_analyzer.py": "# valuation analyzer stub\nprint('valuation analyzer')\n",
    "logs/cron.log": "2024-01-15 07:30:01 INFO Starting daily report\n2024-01-15 07:30:45 INFO Done\n",
    "logs/error.log": "2024-01-14 07:30:12 ERROR yfinance timeout for TSLA\n",
    "notebooks/analysis.ipynb": '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}\n',
    "tests/test_scoring.py": "# placeholder test\ndef test_placeholder():\n    pass\n",
    "docs/architecture.md": "# Architecture\nSee README for details.\n",
    "data/archive/2024-01-14_backup.csv": "ticker,score\nNVDA,72\nAAPL,55\n",
    "data/processed/.gitkeep": "",
    "config/config.example.yaml": (
        "email:\n"
        "  recipients:\n"
        "    - example@email.com\n"
        "portfolio:\n"
        "  - ticker: NVDA\n"
        "    shares: 10\n"
    ),
}
for path, content in distractors.items():
    full = os.path.join(workspace, path)
    with open(full, "w") as f:
        f.write(content)

# ── Main input: messy stocks CSV (has extra columns, inconsistent casing) ─────
stocks_rows = [
    # ticker, company_name, sector, currency, EXTRA_JUNK_COL
    ["NVDA",  "NVIDIA Corporation",       "Technology",      "USD", "ignore_me"],
    ["AAPL",  "Apple Inc",                "Technology",      "USD", "N/A"],
    ["MSFT",  "Microsoft Corporation",    "Technology",      "USD", ""],
    ["JNJ",   "Johnson & Johnson",        "Healthcare",      "USD", "legacy"],
    ["TSM",   "Taiwan Semiconductor Mfg", "Technology",      "TWD", "foreign"],
    ["BRK-B", "Berkshire Hathaway B",     "Financials",      "USD", ""],
    ["VZ",    "Verizon Communications",   "Telecom",         "USD", "old"],
]
with open(os.path.join(workspace, "data/raw/stocks_master.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ticker", "company_name", "sector", "currency", "EXTRA_JUNK_COL"])
    w.writerows(stocks_rows)

# ── Holdings CSV (messy: duplicate entry for NVDA, extra whitespace) ──────────
holdings_rows = [
    # ticker, shares, avg_cost, purchase_date
    ["NVDA",  "50",    "410.2500", "2023-06-01"],
    ["NVDA",  "20",    "480.0000", "2023-11-15"],   # second lot — BOTH must be inserted
    ["AAPL",  "100",   "172.3300", "2022-09-10"],
    ["MSFT",  "30",    "310.7500", "2023-03-22"],
    ["JNJ",   "40",    "155.0000", "2021-12-01"],
    ["BRK-B", "15",    "348.9000", "2022-07-19"],
]
with open(os.path.join(workspace, "data/raw/holdings.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ticker", "shares", "avg_cost", "purchase_date"])
    w.writerows(holdings_rows)

# ── Watchlist CSV ──────────────────────────────────────────────────────────────
watchlist_rows = [
    ["TSM",   "2024-01-10", "Strong fab moat",          "WATCHING"],
    ["VZ",    "2024-01-12", "High dividend yield play",  "WATCHING"],
]
with open(os.path.join(workspace, "data/raw/watchlist.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ticker", "added_date", "reason", "status"])
    w.writerows(watchlist_rows)

# ── Component scores JSON — the agent must apply the proprietary weights ───────
# Each ticker has raw dimension scores (0-100). Agent must compute weighted composite.
# Weights per SKILL.md: valuation=0.30, trend=0.25, macro_sentiment=0.20, technical=0.15, risk=0.10
component_scores = {
    "NVDA":  {"valuation": 80, "trend": 75, "macro_sentiment": 70, "technical": 85, "risk": 60},
    "AAPL":  {"valuation": 60, "trend": 55, "macro_sentiment": 65, "technical": 50, "risk": 70},
    "MSFT":  {"valuation": 55, "trend": 60, "macro_sentiment": 68, "technical": 58, "risk": 75},
    "JNJ":   {"valuation": 45, "trend": 40, "macro_sentiment": 50, "technical": 38, "risk": 65},
    "BRK-B": {"valuation": 30, "trend": 35, "macro_sentiment": 42, "technical": 28, "risk": 55},
}
# Expected composites (for reference — NOT written to workspace):
# NVDA:  0.30*80 + 0.25*75 + 0.20*70 + 0.15*85 + 0.10*60 = 24+18.75+14+12.75+6    = 75.50  → BUY
# AAPL:  0.30*60 + 0.25*55 + 0.20*65 + 0.15*50 + 0.10*70 = 18+13.75+13+7.5+7      = 59.25  → HOLD
# MSFT:  0.30*55 + 0.25*60 + 0.20*68 + 0.15*58 + 0.10*75 = 16.5+15+13.6+8.7+7.5   = 61.30  → HOLD
# JNJ:   0.30*45 + 0.25*40 + 0.20*50 + 0.15*38 + 0.10*65 = 13.5+10+10+5.7+6.5     = 45.70  → WATCH
# BRK-B: 0.30*30 + 0.25*35 + 0.20*42 + 0.15*28 + 0.10*55 = 9+8.75+8.4+4.2+5.5    = 35.85  → SELL

with open(os.path.join(workspace, "data/raw/component_scores.json"), "w") as f:
    json.dump(component_scores, f, indent=2)

# ── Fake old schema file (distractor — wrong column types) ────────────────────
with open(os.path.join(workspace, "data/archive/old_schema.sql"), "w") as f:
    f.write(
        "-- DEPRECATED v0.1 schema\n"
        "CREATE TABLE stocks (ticker TEXT, name TEXT);\n"
        "CREATE TABLE holdings (ticker TEXT, qty FLOAT, cost FLOAT);\n"
    )

print("Workspace generated successfully.")
print(f"Files created under {workspace}/")