import os
import json
import random

random.seed(42)

# Create deeply nested distractor directory structure
dirs = [
    "workspace/client_data/raw",
    "workspace/client_data/processed",
    "workspace/client_data/archive/2022",
    "workspace/client_data/archive/2023",
    "workspace/reports/quarterly",
    "workspace/reports/monthly",
    "workspace/reports/draft",
    "workspace/tools/scripts",
    "workspace/tools/configs",
    "workspace/compliance/kyc",
    "workspace/compliance/audit_logs",
    "workspace/market_data/equities",
    "workspace/market_data/bonds",
    "workspace/tmp",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- DISTRACTOR FILES ---

# Old portfolio format (wrong schema - not the correct input format)
old_portfolio = {
    "holdings": [
        {"symbol": "AAPL", "shares": 100, "cost_basis": 145.00},
        {"symbol": "MSFT", "shares": 75, "cost_basis": 280.00},
    ],
    "cash_balance": 10000
}
with open("workspace/client_data/archive/2022/old_portfolio_format.json", "w") as f:
    json.dump(old_portfolio, f, indent=2)

# Completely wrong file - CSV disguised as JSON
with open("workspace/client_data/raw/export_2023_01.csv", "w") as f:
    f.write("ticker,qty,price\nAAPL,100,150\nTSLA,50,200\n")

# A fake risk report from a different system
with open("workspace/reports/quarterly/legacy_risk_report_Q4_2023.txt", "w") as f:
    f.write("LEGACY RISK REPORT - Q4 2023\nVaR: $12,000 (internal model)\nMax Drawdown: -22%\nNote: This report uses outdated methodology.\n")

# A compliance note file
with open("workspace/compliance/audit_logs/risk_review_notes.txt", "w") as f:
    f.write("Risk committee notes - March 2024:\n- Portfolio needs re-evaluation before board meeting.\n- Last analysis used incorrect benchmark.\n- Client requested SPY benchmark going forward.\n")

# A draft report stub (empty / wrong)
with open("workspace/reports/draft/draft_summary.md", "w") as f:
    f.write("# Draft Risk Summary\n\nTBD - Pending updated analysis.\n")

# A config file for a different tool
with open("workspace/tools/configs/backtest_config.yaml", "w") as f:
    f.write("backtest:\n  start_date: 2020-01-01\n  end_date: 2023-12-31\n  benchmark: QQQ\n  slippage: 0.001\n")

# Fake market data CSV
with open("workspace/market_data/equities/spy_prices_2023.csv", "w") as f:
    f.write("date,open,high,low,close\n2023-01-02,380.1,382.5,378.9,381.5\n2023-01-03,381.0,381.5,376.2,377.1\n")

# A bond portfolio file (wrong asset class, distractor)
with open("workspace/market_data/bonds/bond_positions.json", "w") as f:
    json.dump({"bonds": [{"cusip": "912796TY0", "face_value": 100000, "coupon": 0.045}]}, f, indent=2)

# A Python script that does something unrelated
with open("workspace/tools/scripts/rebalance_calculator.py", "w") as f:
    f.write("# Rebalancing tool - NOT the risk analyzer\n\ndef calculate_rebalance(weights, targets):\n    return {k: targets[k] - weights.get(k, 0) for k in targets}\n")

# A KYC document
with open("workspace/compliance/kyc/client_profile_REDACTED.txt", "w") as f:
    f.write("Client: [REDACTED]\nRisk Tolerance: Moderate-Aggressive\nInvestment Horizon: 5-10 years\nRestrictions: No tobacco, firearms\n")

# A temp file
with open("workspace/tmp/scratch.txt", "w") as f:
    f.write("temp notes: check NVDA correlation with AAPL\n")

# Monthly report placeholder
with open("workspace/reports/monthly/placeholder.txt", "w") as f:
    f.write("Monthly reports - auto-generated. Do not edit manually.\n")

# --- THE ACTUAL PROBLEM INPUT: MESSY/MALFORMED PORTFOLIO FILE ---
# Problems:
#   1. Has extra unknown fields that must be stripped or tolerated
#   2. avg_price field is a string (not float) for some entries  
#   3. Has a duplicate ticker (AAPL appears twice - agent/tool must handle)
#   4. "cash" field is missing (must be added or defaulted)
#   5. One position has quantity as a string
#   6. Has a "metadata" wrapper that doesn't match the expected schema

messy_portfolio = {
    "metadata": {
        "client_id": "C-00492",
        "export_date": "2024-03-15",
        "source": "custody_system_export_v2"
    },
    "positions": [
        {
            "ticker": "AAPL",
            "quantity": "100",
            "avg_price": "150.00",
            "asset_class": "equity",
            "sector": "Technology",
            "country": "US"
        },
        {
            "ticker": "TSLA",
            "quantity": 50,
            "avg_price": 220.50,
            "asset_class": "equity",
            "sector": "Consumer Discretionary",
            "country": "US"
        },
        {
            "ticker": "SPY",
            "quantity": 200,
            "avg_price": "415.75",
            "asset_class": "etf",
            "sector": "Broad Market",
            "country": "US"
        },
        {
            "ticker": "NVDA",
            "quantity": 30,
            "avg_price": 450.00,
            "asset_class": "equity",
            "sector": "Technology",
            "country": "US"
        },
        {
            "ticker": "MSFT",
            "quantity": 60,
            "avg_price": "310.25",
            "asset_class": "equity",
            "sector": "Technology",
            "country": "US"
        },
        {
            "ticker": "AAPL",
            "quantity": 25,
            "avg_price": 170.00,
            "asset_class": "equity",
            "sector": "Technology",
            "country": "US",
            "note": "additional lot purchased Q1 2024"
        },
        {
            "ticker": "JPM",
            "quantity": 40,
            "avg_price": 185.00,
            "asset_class": "equity",
            "sector": "Financials",
            "country": "US"
        }
    ],
    "account_cash": 18500.00,
    "currency": "USD",
    "last_updated": "2024-03-15T09:30:00Z"
}

with open("workspace/client_data/raw/portfolio_export_custody.json", "w") as f:
    json.dump(messy_portfolio, f, indent=2)

print("Sandbox workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("workspace"):
    for file in files:
        print(f"  {os.path.join(root, file)}")