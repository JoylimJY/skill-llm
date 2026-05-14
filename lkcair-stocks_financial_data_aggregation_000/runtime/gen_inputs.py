import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/home/user")

# Create a realistic, deeply nested workspace with distractor files
dirs = [
    "workspace/portfolio/semiconductor",
    "workspace/portfolio/energy",
    "workspace/portfolio/healthcare",
    "workspace/reports/q3_2024",
    "workspace/reports/q2_2024",
    "workspace/data/raw",
    "workspace/data/processed",
    "workspace/scripts/helpers",
    "workspace/config",
    "workspace/archive/2023",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files that look plausible but are wrong/incomplete
distractor_files = {
    "workspace/portfolio/semiconductor/watchlist.txt": (
        "NVDA\nAMD\nINTC\nTSM\nQCOM\n# Semiconductor sector watchlist - Q4 2024\n"
    ),
    "workspace/portfolio/semiconductor/notes.txt": (
        "Review NVDA after earnings. AMD gaining market share.\n"
        "INTC restructuring underway. Consider reducing position.\n"
        "Key metrics to check: P/E ratio, gross margin, revenue growth.\n"
    ),
    "workspace/portfolio/energy/watchlist.txt": "XOM\nCVX\nCOP\n",
    "workspace/portfolio/healthcare/watchlist.txt": "JNJ\nPFE\nABBV\n",
    "workspace/reports/q3_2024/summary.txt": (
        "Q3 2024 Portfolio Summary\n"
        "Total holdings: 47\n"
        "Best performer: NVDA (+12.3%)\n"
        "Worst performer: INTC (-8.1%)\n"
    ),
    "workspace/reports/q2_2024/summary.txt": (
        "Q2 2024 Portfolio Summary\n"
        "Sector rotation into tech and semiconductors.\n"
    ),
    "workspace/data/raw/tickers.csv": (
        "ticker,sector,added_date\n"
        "NVDA,Semiconductors,2022-01-15\n"
        "AMD,Semiconductors,2021-06-10\n"
        "INTC,Semiconductors,2019-03-20\n"
        "AAPL,Technology,2018-05-01\n"
        "MSFT,Technology,2018-05-01\n"
    ),
    "workspace/data/processed/last_run.json": json.dumps({
        "last_updated": "2024-09-15",
        "status": "stale",
        "note": "Data older than 30 days, refresh required"
    }, indent=2),
    "workspace/scripts/helpers/utils.py": (
        "# Utility helpers - placeholder\n"
        "def format_currency(val):\n"
        "    return f'${val:,.2f}'\n"
        "\n"
        "def calc_pct_change(old, new):\n"
        "    if old == 0:\n"
        "        return None\n"
        "    return ((new - old) / old) * 100\n"
    ),
    "workspace/config/settings.json": json.dumps({
        "portfolio_name": "Quantum Growth Fund",
        "manager": "J. Chen",
        "benchmark": "SOX",
        "review_tickers": ["NVDA", "AMD", "INTC"],
        "report_format": "json",
        "output_file": "semiconductor_report.json"
    }, indent=2),
    "workspace/archive/2023/annual_report.txt": (
        "2023 Annual Review\n"
        "Semiconductors outperformed broader market by 34%.\n"
        "Recommendation: maintain overweight position.\n"
    ),
    "workspace/data/raw/failed_fetch_log.txt": (
        "2024-09-10 ERROR: Could not fetch INTC options data\n"
        "2024-09-10 ERROR: Timeout on NVDA fundamentals\n"
        "2024-09-11 INFO: Retry succeeded for NVDA\n"
        "2024-09-12 WARNING: AMD data delayed by 15 minutes\n"
    ),
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content)

# Create a partial/broken attempt at the output file to mislead naive agents
broken_attempt = {
    "error": "incomplete - missing required fields",
    "tickers": ["NVDA", "AMD", "INTC"],
    "comparison": None,
    "note": "This file was auto-generated but failed. Do not use."
}
(workspace / "workspace/portfolio/semiconductor/semiconductor_report_OLD.json").write_text(
    json.dumps(broken_attempt, indent=2)
)

print("Workspace generated successfully.")
print(f"Distractor files created: {len(distractor_files) + 1}")