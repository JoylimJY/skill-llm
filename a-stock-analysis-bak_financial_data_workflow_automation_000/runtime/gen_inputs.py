#!/usr/bin/env python3
import os
import json
import random
import csv
from pathlib import Path

random.seed(42)
workspace = Path("/workspace")

# Create realistic distractor directory structure
dirs = [
    "reports/2024/Q3",
    "reports/2024/Q4",
    "data/raw",
    "data/processed",
    "configs",
    "logs",
    "scripts/utils",
    "archive/old_positions",
    "notes",
    "exports",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but irrelevant
(workspace / "configs" / "app.yaml").write_text("""\
database:
  host: localhost
  port: 5432
  name: trading_db
cache:
  ttl: 300
  backend: redis
""")

(workspace / "configs" / "trading_params.json").write_text(json.dumps({
    "risk_limit": 0.05,
    "max_position_size": 100000,
    "stop_loss_pct": 0.08,
    "take_profit_pct": 0.15,
    "trading_hours": "09:30-15:00"
}, indent=2))

(workspace / "logs" / "trading.log").write_text("""\
2024-01-15 09:30:01 INFO Market opened
2024-01-15 09:31:22 INFO Fetching quotes for watchlist
2024-01-15 09:32:05 WARN Rate limit approaching
2024-01-15 10:15:43 INFO Order submitted: BUY 002714 @ 178.50
2024-01-15 14:30:01 INFO Closing session
""")

(workspace / "logs" / "errors.log").write_text("""\
2024-01-10 10:00:01 ERROR Connection timeout for code 600036
2024-01-11 09:31:00 ERROR Parse error in response
""")

(workspace / "reports" / "2024" / "Q3" / "summary.txt").write_text("""\
Q3 2024 Portfolio Performance Summary
Period: July 1 - September 30
Total Return: +8.3%
Benchmark (CSI 300): +2.1%
Alpha: +6.2%
""")

(workspace / "reports" / "2024" / "Q4" / "watchlist.txt").write_text("""\
Q4 2024 Watchlist
High conviction: 600519, 002714, 000858
Medium conviction: 601318, 600036, 000333
Watch: 300750, 002594
""")

(workspace / "data" / "raw" / "price_history.csv").write_text("""\
date,code,open,high,low,close,volume
2024-01-02,600789,10.20,10.55,10.10,10.42,1520000
2024-01-03,600789,10.42,10.68,10.35,10.57,1830000
2024-01-04,600789,10.57,10.72,10.40,10.48,1210000
2024-01-02,002446,8.32,8.55,8.28,8.50,980000
2024-01-03,002446,8.50,8.62,8.44,8.58,1100000
""")

(workspace / "data" / "processed" / "indicators.json").write_text(json.dumps({
    "600789": {"ma5": 10.45, "ma10": 10.38, "rsi": 58.3, "macd": 0.12},
    "002446": {"ma5": 8.52, "ma10": 8.47, "rsi": 61.2, "macd": 0.08},
}, indent=2))

(workspace / "archive" / "old_positions" / "2023_positions.json").write_text(json.dumps({
    "600030": {"code": "600030", "cost": 18.50, "qty": 2000, "status": "closed"},
    "601166": {"code": "601166", "cost": 14.20, "qty": 5000, "status": "closed"},
    "000001": {"code": "000001", "cost": 11.80, "qty": 3000, "status": "closed"},
}, indent=2))

(workspace / "scripts" / "utils" / "helpers.py").write_text("""\
# Utility helpers for data processing
import json
from pathlib import Path

def load_json(filepath):
    with open(filepath) as f:
        return json.load(f)

def format_number(n, decimals=2):
    return f'{n:.{decimals}f}'
""")

(workspace / "notes" / "strategy_notes.md").write_text("""\
# Trading Strategy Notes

## Entry Criteria
- RSI < 30 oversold signal
- Volume > 2x 5-day average
- Price above MA20

## Exit Criteria
- RSI > 70
- Stop loss at -8%
- Take profit at +15%

## Watch for:
- Pre-market volume spikes
- Institutional buying patterns
- Sector rotation signals
""")

(workspace / "exports" / "placeholder.txt").write_text("Export directory for generated reports\n")

# THE ACTUAL TASK INPUT: A CSV file with holdings the agent needs to import
# This is messy real-world data - the agent must translate it into portfolio commands
holdings_data = [
    {"stock_code": "600789", "stock_name": "鲁抗医药",    "avg_cost": 10.416, "quantity": 3400,  "action": "add"},
    {"stock_code": "002446", "stock_name": "盛路通信",    "avg_cost": 8.320,  "quantity": 5800,  "action": "add"},
    {"stock_code": "002342", "stock_name": "巨星科技",    "avg_cost": 14.750, "quantity": 2000,  "action": "add"},
    {"stock_code": "300750", "stock_name": "宁德时代",    "avg_cost": 185.600,"quantity": 500,   "action": "add"},
    {"stock_code": "000858", "stock_name": "五粮液",      "avg_cost": 143.200,"quantity": 300,   "action": "add_then_remove"},  # add then remove
    {"stock_code": "600789", "stock_name": "鲁抗医药",    "avg_cost": 10.250, "quantity": 3400,  "action": "update_cost"},  # update cost for 600789
]

with open(workspace / "data" / "raw" / "current_holdings.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["stock_code", "stock_name", "avg_cost", "quantity", "action"])
    writer.writeheader()
    writer.writerows(holdings_data)

# Instructions file - describes what needs to be done in business terms
(workspace / "task_brief.txt").write_text("""\
Portfolio Setup & Analysis Task
================================

Please perform the following portfolio operations using the available stock analysis tools:

1. Add the following initial holdings to the portfolio tracker:
   - 600789 (鲁抗医药): cost 10.416, quantity 3400
   - 002446 (盛路通信): cost 8.320, quantity 5800  
   - 002342 (巨星科技): cost 14.750, quantity 2000
   - 300750 (宁德时代): cost 185.600, quantity 500
   - 000858 (五粮液): cost 143.200, quantity 300

2. Remove 000858 (五粮液) from the portfolio (decided to exit this position)

3. Update the average cost for 600789 to 10.250 (averaged down)

4. Generate a real-time JSON analysis report for the 3 core holdings:
   600789, 002446, 002342
   Save the output to a file named: stock_analysis_report.json

The raw holdings data is available in: data/raw/current_holdings.csv
""")

print("Workspace generated successfully")
print(f"Files created in: {workspace}")