import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Create distractor directory structure ---
dirs = [
    "research/china/banks",
    "research/china/tech",
    "research/us/macro",
    "research/us/equities",
    "research/forex",
    "archive/2024/q4",
    "archive/2025/q1",
    "config/providers",
    "config/schedules",
    "scripts/helpers",
    "output/drafts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files (realistic but misleading) ---
distractor_files = {
    "research/china/banks/watchlist.csv": "symbol,name,sector\n600036,招商银行,银行\n601318,中国平安,保险\n000001,平安银行,银行\n",
    "research/china/tech/notes.txt": "Tech sector rotation analysis - pending data pull.\nDo NOT use yfinance for A-shares.",
    "research/us/macro/fred_codes.txt": "FEDFUNDS - Effective Fed Funds Rate\nDFEDTARU - Fed Funds Target Upper\nGDP - Gross Domestic Product\nCPIAUCSL - CPI All Urban Consumers\nUNRATE - Unemployment Rate\n",
    "research/us/equities/sp500_tickers.txt": "AAPL\nMSFT\nNVDA\nGOOGL\nAMZN\n",
    "research/forex/pairs_of_interest.txt": "EURUSD - Primary pair for EUR/USD analysis\nGBPUSD - Sterling cable\nUSDJPY - Dollar Yen\nUSDCNY - Dollar Offshore Yuan\n",
    "archive/2024/q4/quarterly_report_draft.json": json.dumps({"quarter": "Q4-2024", "status": "draft", "data": {}}),
    "archive/2025/q1/template_morning_brief.json": json.dumps({
        "date": "2025-01-01",
        "assets": {
            "a_share": "PLACEHOLDER",
            "fed_rate": "PLACEHOLDER",
            "eurusd": "PLACEHOLDER"
        },
        "note": "This is a template only - do not use as final output"
    }, indent=2),
    "config/providers/provider_map.yaml": "# Provider mapping\na_share: akshare\nus_equity: yfinance\nforex: yfinance\nmacro: fred\n",
    "config/schedules/daily_jobs.txt": "07:00 - Pull A-share premarket data\n07:30 - Pull FRED macro series\n08:00 - Pull forex data\n08:30 - Generate morning brief\n",
    "scripts/helpers/symbol_formatter.py": "# NOT a working script - placeholder only\ndef format_symbol(s, market):\n    if market == 'cn': return s.zfill(6)\n    if market == 'fx': return s + '=X'\n    return s\n",
    "output/drafts/morning_brief_BROKEN.json": json.dumps({
        "error": "Wrong provider used for A-share query",
        "symbol_used": "600036",
        "provider_used": "yfinance",
        "result": None
    }, indent=2),
    "research/china/banks/sector_analysis_stub.txt": "招商银行 (600036) - CMB - Major retail bank\nData source: Must use AKShare for A-share market data.\nDo not confuse with HK listing.\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- The task specification file (business requirement, no tool hints) ---
task_spec = {
    "task": "Global Macro Morning Brief Generation",
    "requested_by": "Portfolio Manager, Global Macro Desk",
    "date_requested": "2025-07-10",
    "assets_to_cover": [
        {
            "description": "China A-share: CMB (招商银行)",
            "identifier": "600036",
            "market": "Shanghai Stock Exchange",
            "data_needed": "Historical price data, most recent 30 trading days"
        },
        {
            "description": "US Federal Reserve Policy Rate",
            "identifier": "DFEDTARU",
            "market": "FRED Macro Database",
            "data_needed": "Series from 2025-01-01 onwards"
        },
        {
            "description": "Forex: Euro vs US Dollar",
            "identifier": "EUR/USD",
            "market": "Global FX Market",
            "data_needed": "Historical daily data from 2025-03-01"
        }
    ],
    "output_requirements": {
        "filename": "morning_brief.json",
        "format": "JSON",
        "must_include": [
            "timestamp of report generation",
            "results for each of the 3 assets",
            "the exact mcp commands used to retrieve the data"
        ]
    }
}

with open(os.path.join(workspace, "task_specification.json"), "w") as f:
    json.dump(task_spec, f, indent=2, ensure_ascii=False)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1}")