import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deeply nested distractor structure ---
dirs = [
    "workspace/portfolio/equities/tech",
    "workspace/portfolio/equities/energy",
    "workspace/portfolio/crypto/defi",
    "workspace/portfolio/crypto/layer1",
    "workspace/reports/weekly",
    "workspace/reports/monthly",
    "workspace/data/raw/prices",
    "workspace/data/raw/news",
    "workspace/data/processed",
    "workspace/config/api",
    "workspace/config/alerts",
    "workspace/scripts/legacy",
    "workspace/scripts/analysis",
    "workspace/logs/2024",
]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/portfolio/equities/tech/holdings.csv": "ticker,shares,avg_cost\nNVDA,500,220.50\nAAPL,300,175.20\nMSFT,200,310.80\n",
    "workspace/portfolio/equities/energy/holdings.csv": "ticker,shares,avg_cost\nXOM,100,110.30\nCVX,150,155.00\n",
    "workspace/portfolio/crypto/defi/positions.json": json.dumps({"UNI": 1000, "AAVE": 500, "CRV": 2000}),
    "workspace/portfolio/crypto/layer1/positions.json": json.dumps({"ETH": 10, "SOL": 200, "DOT": 500}),
    "workspace/reports/weekly/report_2024_01_15.txt": "Weekly summary: Markets volatile. Tech led gains.\n",
    "workspace/reports/monthly/january_2024.txt": "Monthly performance: Portfolio up 4.2%.\n",
    "workspace/data/raw/prices/old_prices.csv": "date,open,high,low,close,volume\n2023-01-02,143.0,145.0,141.5,144.3,75000000\n",
    "workspace/data/raw/news/scraped_headlines.txt": "NVDA smashes earnings\nBitcoin ETF approved\nFed holds rates\n",
    "workspace/data/processed/cleaned_data.json": json.dumps({"status": "processed", "records": 1024}),
    "workspace/config/api/endpoints.yaml": "market_data:\n  base_url: http://localhost:8765\n  version: v1\n",
    "workspace/config/alerts/thresholds.json": json.dumps({"nvda_drop_pct": 5.0, "btc_drop_pct": 10.0}),
    "workspace/scripts/legacy/fetch_prices.py": "# deprecated\nimport requests\n# old logic\n",
    "workspace/scripts/analysis/momentum.py": "# momentum scoring script\nimport pandas as pd\n",
    "workspace/logs/2024/app.log": "[2024-03-15 09:00:01] INFO: Market data fetch started\n[2024-03-15 09:00:05] INFO: Fetch complete\n",
}

for filepath, content in distractor_files.items():
    p = Path(filepath)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# A misleading "briefing_template.json" that has WRONG field names to trap naive agents
template = {
    "briefing_date": "YYYY-MM-DD",
    "equity_data": {
        "note": "PLACEHOLDER - fill with actual weekly OHLCV for NVDA",
        "symbol": "NVDA",
        "interval": "weekly",
        "start": "TBD",
        "end": "TBD",
        "records": []
    },
    "crypto_data": {
        "note": "PLACEHOLDER - fill with ETH price in EUR",
        "token_id": "ETH",
        "price_eur": None
    },
    "macro_events": {
        "note": "PLACEHOLDER - high impact USD events",
        "filter": "impact=high, currency=usd",
        "events": []
    }
}
Path("workspace/reports/weekly/briefing_template.json").write_text(json.dumps(template, indent=2))

# A fake "market_data_config.json" with wrong parameter names to mislead
bad_config = {
    "get_stock": {"symbol": "NVDA", "frequency": "weekly", "from": "2024-01-01"},
    "get_crypto": {"coin": "ETH", "fiat": "EUR"},
    "calendar": {"level": "high", "ccy": "USD"}
}
Path("workspace/config/api/market_data_config.json").write_text(json.dumps(bad_config, indent=2))

print("Workspace generated successfully.")