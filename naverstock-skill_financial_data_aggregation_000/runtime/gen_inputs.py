import os
import json
import random
import csv

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure ────────────────────────────────────────────────
dirs = [
    "archive/2023/Q4",
    "archive/2024/Q1",
    "archive/2024/Q2",
    "reports/daily",
    "reports/weekly",
    "config",
    "scripts",
    "data/raw",
    "data/processed",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────

# 1. Old stale price snapshots (wrong format, outdated)
stale_snapshot = {
    "timestamp": "2024-01-15T09:00:00Z",
    "prices": {
        "005930": 71200,
        "AAPL": 185.20,
        "TSLA": 220.10,
    },
    "note": "Manual snapshot - DO NOT USE FOR LIVE REPORTING"
}
with open(os.path.join(workspace, "archive/2024/Q1/stale_prices.json"), "w") as f:
    json.dump(stale_snapshot, f, indent=2)

# 2. Broken JSON distractor
with open(os.path.join(workspace, "archive/2024/Q2/broken_snapshot.json"), "w") as f:
    f.write('{"prices": {"005930": 69000, "TSLA": INVALID_VALUE}, "status": "corrupt"}')

# 3. Old portfolio format (CSV with wrong columns - distractor)
with open(os.path.join(workspace, "archive/2023/Q4/old_portfolio.csv"), "w") as f:
    f.write("ticker,avg_cost,market_value\n")
    f.write("005930,68000,6800000\n")
    f.write("AAPL,150.0,15000.0\n")

# 4. Config files (distractors)
with open(os.path.join(workspace, "config/market_hours.json"), "w") as f:
    json.dump({
        "KRX": {"open": "09:00", "close": "15:30"},
        "NYSE": {"open": "09:30", "close": "16:00"},
        "note": "Regular hours only"
    }, f, indent=2)

with open(os.path.join(workspace, "config/currency_map.json"), "w") as f:
    json.dump({
        "KRW": "Korean Won",
        "USD": "US Dollar",
        "JPY": "Japanese Yen"
    }, f, indent=2)

# 5. Shell script distractors
with open(os.path.join(workspace, "scripts/fetch_old.sh"), "w") as f:
    f.write("#!/bin/bash\n# Deprecated fetcher - uses old API endpoint\ncurl 'https://old-api.example.com/stock?code=$1'\n")

with open(os.path.join(workspace, "scripts/cleanup.sh"), "w") as f:
    f.write("#!/bin/bash\nrm -rf /workspace/data/raw/*.tmp\necho 'Cleaned temp files'\n")

# 6. Partial processed data (distractor)
with open(os.path.join(workspace, "data/processed/partial_report.json"), "w") as f:
    json.dump({
        "generated": "2024-06-01",
        "stocks": [
            {"code": "005930", "price": 78000, "nxtPrice": None}
        ],
        "status": "incomplete"
    }, f, indent=2)

# 7. Raw log files
with open(os.path.join(workspace, "logs/fetch_errors.log"), "w") as f:
    f.write("2024-06-01 09:01:22 ERROR: Timeout fetching TSLA\n")
    f.write("2024-06-01 09:01:45 ERROR: Unknown symbol XYZ\n")
    f.write("2024-06-01 09:02:10 INFO: Retry success for TSLA\n")

with open(os.path.join(workspace, "logs/system.log"), "w") as f:
    f.write("2024-06-01 08:55:00 INFO: Market pre-open check started\n")
    f.write("2024-06-01 09:00:00 INFO: KRX market opened\n")

# 8. Weekly summary (distractor, wrong schema)
with open(os.path.join(workspace, "reports/weekly/week23_summary.json"), "w") as f:
    json.dump({
        "week": 23,
        "topGainer": "삼성전자",
        "topLoser": "카카오",
        "avgChange": 1.3
    }, f, indent=2)

# 9. Daily placeholder
with open(os.path.join(workspace, "reports/daily/placeholder.txt"), "w") as f:
    f.write("Daily reports are generated automatically. Do not edit manually.\n")

# 10. Data raw temp file
with open(os.path.join(workspace, "data/raw/feed_20240601.tmp"), "w") as f:
    f.write("RAW_BINARY_FEED_PLACEHOLDER\x00\x01\x02")

# ── THE ACTUAL INPUT: portfolio.csv ───────────────────────────────────
# Mix of: Korean name, KRX code, overseas ticker, exchange rate symbol
# Columns: identifier, shares
portfolio = [
    ("삼성전자", 50),    # domestic by Korean name
    ("005935", 30),      # Samsung Electronics preferred (KRX code)
    ("AAPL", 10),        # overseas by ticker
    ("Tesla", 5),        # overseas by English name
    ("USD", 0),          # exchange rate (shares=0, value tracking only)
]

with open(os.path.join(workspace, "portfolio.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["identifier", "shares"])
    for identifier, shares in portfolio:
        writer.writerow([identifier, shares])

print("Workspace initialized successfully.")
print(f"portfolio.csv created with {len(portfolio)} entries.")