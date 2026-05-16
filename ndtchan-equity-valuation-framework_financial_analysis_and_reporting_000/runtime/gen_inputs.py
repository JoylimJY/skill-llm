import os
import json
import random

random.seed(42)

base = "/workspace"

# ── Directory structure with distractors ──────────────────────────────────────
dirs = [
    "data/raw/prices",
    "data/raw/fundamentals",
    "data/processed",
    "data/peers",
    "reports/drafts",
    "reports/archived",
    "models/dcf_templates",
    "models/multiples",
    "macro/vn",
    "macro/global",
    "scripts",
    "config",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "data/raw/prices/HSG_daily.json": json.dumps(
        {"ticker": "HSG", "prices": [random.uniform(15000, 25000) for _ in range(20)]}
    ),
    "data/raw/prices/NKG_daily.csv": "date,close\n2024-01-02,18500\n2024-01-03,18750\n",
    "data/raw/fundamentals/HSG_2023.json": json.dumps(
        {"ticker": "HSG", "revenue": 28500, "net_income": 420, "total_assets": 21000}
    ),
    "data/peers/steel_sector_medians.csv": (
        "metric,median\nP/E,9.2\nP/B,1.1\nEV/EBITDA,6.8\n"
    ),
    "data/processed/macro_vn_Q1_2024.json": json.dumps(
        {"gdp_growth": 5.6, "cpi": 3.1, "policy_rate_pct": 4.5}
    ),
    "reports/archived/HPG_2022_memo.txt": (
        "Archived memo from 2022. DO NOT USE. HPG was trading at P/E 7x in 2022.\n"
    ),
    "reports/drafts/incomplete_template.md": (
        "# Valuation Draft\n## Section A\nTBD\n## Section B\nTBD\n"
    ),
    "models/dcf_templates/generic_dcf.xlsx.stub": "STUB FILE - not a real spreadsheet",
    "models/multiples/regression_multiples.py": (
        "# Placeholder regression script\ndef run(): pass\n"
    ),
    "macro/global/fed_rates_2024.json": json.dumps(
        {"fed_funds_rate": 5.25, "10y_treasury": 4.45}
    ),
    "macro/vn/sbv_rates.json": json.dumps(
        {"refinancing_rate": 4.5, "discount_rate": 3.0, "as_of": "2024-03-01"}
    ),
    "scripts/fetch_vnstock.py": "# Script for fetching vnstock data\n# Not relevant to this task\n",
    "config/valuation_params.yaml": (
        "default_horizon: 5\nrisk_free_rate: 4.5\nERP: 7.5\nbeta_default: 1.2\n"
    ),
    "logs/agent_run_20240101.log": "INFO: previous run completed\nWARN: stale data detected\n",
}

for path, content in distractors.items():
    full_path = os.path.join(base, path)
    with open(full_path, "w") as f:
        f.write(content)

# ── PRIMARY INPUT: Messy, partially incomplete HPG bundle ────────────────────
# Deliberate issues:
#   1. cash_flow section is empty (CFO missing) → must be flagged
#   2. balance_sheet: assets ≠ liabilities + equity (minor inconsistency)
#   3. as_of_date is ~8 months stale relative to a "today" of 2024-11-01
#   4. P/E and EV/EBITDA in ratios, but EPS is missing from income_statement
#   5. price_history returns: 6m and 12m are null

hpg_bundle = {
    "ticker": "HPG",
    "as_of_date": "2024-03-15",
    "currency": "VND",
    "financials": {
        "income_statement": {
            "period": "FY2023",
            "revenue_bn": 140200,
            "gross_profit_bn": 18650,
            "ebit_bn": 9800,
            "ebitda_bn": 14200,
            "net_income_bn": 6900,
            "interest_expense_bn": 2100,
            "tax_rate_pct": 20.0,
            "shares_outstanding_mn": 4680,
            "note": "EPS not separately provided; derive from net_income / shares"
        },
        "balance_sheet": {
            "period": "FY2023",
            "total_assets_bn": 115000,
            "total_liabilities_bn": 71000,
            "total_equity_bn": 43500,
            "net_debt_bn": 28400,
            "note": "INCONSISTENCY: assets(115000) != liabilities(71000) + equity(43500) = 114500; delta=500bn"
        },
        "cash_flow": {},
        "ratios": {
            "trailing_pe": 7.8,
            "pb_ratio": 1.05,
            "ev_ebitda": 6.2,
            "roe_pct": 15.9,
            "debt_to_equity": 1.63,
            "current_ratio": 1.18,
            "note": "CFO-based ratios unavailable due to missing cash flow statement"
        }
    },
    "price_history": {
        "daily": [
            {"date": "2024-03-15", "close": 27500},
            {"date": "2024-03-14", "close": 27200},
            {"date": "2024-03-13", "close": 26900},
        ],
        "returns": {
            "1m": 0.032,
            "3m": 0.071,
            "6m": None,
            "12m": None
        }
    },
    "peer_set": ["HSG", "NKG", "TLH"],
    "peer_multiples": {
        "HSG": {"pe": 9.1, "pb": 0.92, "ev_ebitda": 7.1},
        "NKG": {"pe": 10.3, "pb": 1.08, "ev_ebitda": 7.8},
        "TLH": {"pe": 8.7, "pb": 0.85, "ev_ebitda": 6.5},
        "sector_median": {"pe": 9.2, "pb": 0.95, "ev_ebitda": 7.1}
    },
    "macro_snapshot": {
        "vn_gdp_growth_2024f": 5.8,
        "inflation_pct": 3.2,
        "sbv_rate_pct": 4.5,
        "steel_demand_outlook": "moderate recovery; infrastructure spending supportive",
        "global_steel_oversupply_risk": "elevated due to China export surge",
        "note": "Macro data as of 2024-Q1"
    },
    "news_digest": {
        "recent_headlines": [
            "HPG announces capacity expansion at Dung Quat 2 phase; completion 2026",
            "China steel dumping pressure on Vietnamese producers intensifies",
            "MoF proposes safeguard tariff extension for HRC imports",
            "HPG Q1-2024 earnings beat: net profit up 22% YoY on volume"
        ],
        "sentiment": "mixed"
    },
    "metadata": {
        "source": "vci",
        "data_quality_notes": [
            "Cash flow statement not available for FY2023 full year",
            "Balance sheet equity figure may include minority interest",
            "Price data cut-off: 2024-03-15; report generated 2024-03-16"
        ]
    }
}

input_path = os.path.join(base, "data", "raw", "fundamentals", "HPG_valuation_bundle.json")
with open(input_path, "w", encoding="utf-8") as f:
    json.dump(hpg_bundle, f, indent=2, ensure_ascii=False)

print("Workspace generated successfully.")
print(f"Primary input: {input_path}")