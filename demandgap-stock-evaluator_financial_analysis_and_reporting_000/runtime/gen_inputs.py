import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic deeply nested distractor structure
distractor_dirs = [
    "archive/2022/Q1", "archive/2022/Q2", "archive/2023/Q3",
    "reports/internal/drafts", "reports/published",
    "data/raw/market_feeds", "data/processed",
    "templates/legacy", "templates/current",
    "scripts/deprecated",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "archive/2022/Q1/AAPL_old_analysis.md": "# Apple Inc - Q1 2022\nOLD ANALYSIS - DEPRECATED\nDo not use this file.",
    "archive/2022/Q2/MSFT_brief.txt": "MSFT Q2 2022: Revenue $51.9B, EPS $2.23. Archived.",
    "archive/2023/Q3/watchlist.csv": "TICKER,SECTOR,DATE_ADDED\nNVDA,Tech,2023-01-15\nTSLA,Auto,2023-03-22\nAMZN,Retail,2023-06-01",
    "reports/internal/drafts/template_v1.md": "## DRAFT TEMPLATE\nThis is an old template. Do NOT use.",
    "reports/published/GOOG_2023.pdf.txt": "Google 2023 Annual Analysis - Published. See attached PDF (not available here).",
    "data/raw/market_feeds/sp500_daily.csv": "date,close\n2024-01-02,4742.83\n2024-01-03,4704.81\n2024-01-04,4688.68",
    "data/processed/sector_pe_ratios.json": json.dumps({"Technology": 28.5, "Healthcare": 22.1, "Energy": 12.3, "Financials": 14.8}),
    "templates/legacy/old_dashboard.jsx": "// DEPRECATED - Do not use this template\nconst OldDashboard = () => <div>Old</div>;",
    "templates/current/README_IGNORE.txt": "This folder is empty. New templates are in SKILL.md.",
    "scripts/deprecated/fetch_data.py": "# DEPRECATED SCRIPT\n# import yfinance as yf\n# This script no longer works.",
    "data/raw/market_feeds/vix_data.csv": "date,vix\n2024-11-01,18.5\n2024-11-15,19.2\n2024-12-01,17.8",
}
for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# THE MAIN INPUT: A realistic raw financial data file for a fictional company
# Company: "NordStar Logistics AG" - Ticker: NSLG
# This is the messy raw data the agent must work with

financial_data = {
    "company": {
        "name": "NordStar Logistics AG",
        "ticker": "NSLG",
        "exchange": "XETRA",
        "currency": "EUR",
        "sector": "Industrials",
        "industry": "Freight & Logistics",
        "description": "NordStar Logistics AG provides end-to-end freight forwarding, last-mile delivery, and cold-chain logistics services across Northern and Central Europe. The company operates a fleet of 3,200 vehicles and partners with 47 regional distribution centers.",
        "analysis_date": "2025-07-15"
    },
    "price_data": {
        "current_price": 42.85,
        "52w_high": 58.20,
        "52w_low": 34.10,
        "price_6m_ago": 37.50,
        "price_12m_ago": 51.30,
        "peak_5y": 61.40,
        "trough_5y": 28.90,
        "ma_50d": 40.12,
        "ma_200d": 44.78,
        "rsi_14": 48.3,
        "beta": 1.24,
        "vol_1y_pct": 31.2,
        "market_cap_eur_billions": 3.42
    },
    "income_statement": {
        "revenue_fy2024": 4_820_000_000,
        "revenue_fy2023": 4_721_000_000,
        "revenue_fy2022": 5_102_000_000,
        "revenue_fy2021": 4_650_000_000,
        "revenue_fy2020": 3_890_000_000,
        "net_income_fy2024": 289_200_000,
        "net_income_fy2023": 261_800_000,
        "net_income_fy2022": 357_400_000,
        "gross_profit_fy2024": 1_494_200_000,
        "operating_income_fy2024": 434_880_000,
        "ebit_fy2024": 434_880_000,
        "interest_expense_fy2024": 48_200_000,
        "depreciation_amortization_fy2024": 182_000_000,
        "eps_ttm": 3.62,
        "forward_eps": 3.91,
        "shares_outstanding_millions": 79.8,
        "shares_outstanding_prior_year_millions": 79.8
    },
    "balance_sheet": {
        "total_assets_fy2024": 5_610_000_000,
        "total_assets_fy2023": 5_380_000_000,
        "current_assets_fy2024": 1_682_000_000,
        "current_assets_fy2023": 1_598_000_000,
        "current_liabilities_fy2024": 1_121_000_000,
        "current_liabilities_fy2023": 1_089_000_000,
        "total_liabilities_fy2024": 3_220_000_000,
        "long_term_debt_fy2024": 1_540_000_000,
        "long_term_debt_fy2023": 1_620_000_000,
        "total_equity_fy2024": 2_390_000_000,
        "retained_earnings_fy2024": 1_890_000_000,
        "cash_and_equivalents_fy2024": 412_000_000,
        "total_debt_fy2024": 1_870_000_000,
        "working_capital_fy2024": 561_000_000,
        "working_capital_fy2023": 509_000_000,
        "gross_margin_fy2023_pct": 29.8,
        "gross_margin_fy2024_pct": 31.0
    },
    "cash_flow": {
        "operating_cf_fy2024": 521_400_000,
        "operating_cf_fy2023": 498_200_000,
        "capex_fy2024": 198_000_000,
        "fcf_fy2024": 323_400_000,
        "fcf_fy2023": 301_500_000,
        "fcf_fy2022": 285_000_000,
        "fcf_fy2021": 260_000_000,
        "fcf_fy2020": 198_000_000,
        "dividends_paid_fy2024": 63_840_000
    },
    "derived_ratios_raw": {
        "roe_fy2024_pct": 12.1,
        "roa_fy2023_pct": 4.6,
        "asset_turnover_fy2023": 0.878,
        "asset_turnover_fy2024": 0.859,
        "short_interest_pct": 3.8,
        "news_sentiment_score": 0.142,
        "news_article_count": 23,
        "analyst_price_target_eur": 51.20,
        "subsector_pe": 17.5,
        "insider_buys_12m": 3,
        "insider_sells_12m": 1,
        "net_insider_shares_k": "+42K"
    },
    "altman_inputs_note": "Use standard public-company Altman Z-Score formula: Z = 1.2*(WC/TA) + 1.4*(RE/TA) + 3.3*(EBIT/TA) + 0.6*(MarketCap/TotalLiabilities) + 1.0*(Sales/TA). All values available in balance_sheet and income_statement above.",
    "historical_price_series": [
        {"year": "2015", "price": 18.40},
        {"year": "2016", "price": 21.80},
        {"year": "2017", "price": 26.50},
        {"year": "2018", "price": 31.20},
        {"year": "2019", "price": 38.90},
        {"year": "2020", "price": 29.40},
        {"year": "2021", "price": 48.70},
        {"year": "2022", "price": 55.30},
        {"year": "2023", "price": 51.30},
        {"year": "2024", "price": 46.20},
        {"year": "2025", "price": 42.85}
    ],
    "peers": [
        {"ticker": "DHER.DE", "name": "DHL Group", "market_cap_b": 38.2, "rev_growth_pct": 2.1, "profit_margin_pct": 4.8, "roe_pct": 28.5, "pe": 14.2, "moat": "Wide"},
        {"ticker": "KNIN.SW", "name": "Kuehne+Nagel", "market_cap_b": 21.8, "rev_growth_pct": -4.2, "profit_margin_pct": 7.1, "roe_pct": 35.2, "pe": 18.6, "moat": "Narrow"},
        {"ticker": "DSV.CO", "name": "DSV A/S", "market_cap_b": 29.4, "rev_growth_pct": 1.8, "profit_margin_pct": 6.2, "roe_pct": 16.8, "pe": 20.1, "moat": "Narrow"},
        {"ticker": "XPO", "name": "XPO Inc", "market_cap_b": 11.2, "rev_growth_pct": 3.4, "profit_margin_pct": 3.1, "roe_pct": 22.1, "pe": 22.5, "moat": "Narrow"}
    ],
    "technical_notes": {
        "support_1": 40.00,
        "support_2": 36.50,
        "resistance_1": 46.00,
        "resistance_2": 50.80,
        "macd_line": -0.82,
        "macd_signal": -0.45,
        "macd_histogram": -0.37,
        "trend": "Downtrend"
    },
    "dcf_assumptions": {
        "wacc_pct": 9.5,
        "terminal_growth_pct": 2.5,
        "fcf_growth_y1_y5_pct": 8.0,
        "margin_of_safety_pct": 20
    },
    "beneish_components": {
        "days_sales_outstanding_index": 1.04,
        "gross_margin_index": 0.96,
        "asset_quality_index": 1.08,
        "sales_growth_index": 1.021,
        "depreciation_index": 0.97,
        "sga_index": 1.02,
        "leverage_index": 0.95,
        "total_accruals_to_assets": 0.038,
        "note": "M-Score = -4.84 + (-0.920 * DSRI) + (0.528 * GMI) + (0.404 * AQI) + (0.892 * SGI) + (0.115 * DEPI) + (-0.172 * SGAI) + (4.679 * TATA) + (-0.327 * LVGI)"
    },
    "valuation_data": {
        "pb_ratio": 1.43,
        "ps_ratio": 0.71,
        "ev_ebitda": 8.9,
        "dividend_per_share": 0.80,
        "years_paying_dividends": 8,
        "years_positive_earnings": 7,
        "earnings_predictability_score": 72.0
    }
}

input_path = os.path.join(workspace, "NSLG_raw_financial_data.json")
with open(input_path, "w") as f:
    json.dump(financial_data, f, indent=2)

# A second distractor file that looks similar but is for a different company
distractor_financial = {
    "company": {"name": "SunBridge Capital Partners", "ticker": "SBCP", "note": "INTERNAL USE ONLY - NOT FOR ANALYSIS"},
    "status": "INCOMPLETE - data collection in progress",
    "price_data": {"current_price": 88.20},
}
with open(os.path.join(workspace, "data/raw/SBCP_incomplete_data.json"), "w") as f:
    json.dump(distractor_financial, f, indent=2)

# A partially-filled wrong analysis as a distractor
wrong_analysis = """# NSLG - NordStar Logistics AG
## INCOMPLETE DRAFT - DO NOT SUBMIT

ROE: 12.1%  
Operating Margin: 9.02%  (NOTE: wrong label used here)
Recommendation: HOLD

THIS DRAFT WAS ABANDONED - metrics are wrong, do not use.
"""
with open(os.path.join(workspace, "reports/internal/drafts/NSLG_draft_WRONG.md"), "w") as f:
    f.write(wrong_analysis)

print("Workspace initialized successfully.")
print(f"Main input file: {input_path}")
print(f"Total distractor files: {len(distractors) + 2}")