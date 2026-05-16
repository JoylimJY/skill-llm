import os
import json
import random

random.seed(42)

# Create directory structure
dirs = [
    "workspace/scripts",
    "workspace/data/raw",
    "workspace/data/processed",
    "workspace/reports/archive",
    "workspace/config",
    "workspace/logs",
    "workspace/notebooks",
    "workspace/tests",
    "workspace/utils",
    "workspace/cache",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ---- Distractor files ----

# Old/stale report (distractor)
stale_report = {
    "generated_at": "2023-01-01",
    "note": "This is an outdated report. Please regenerate.",
    "funds": []
}
with open("workspace/reports/archive/old_equity_report_2023.json", "w") as f:
    json.dump(stale_report, f, ensure_ascii=False, indent=2)

# Random config file (distractor)
with open("workspace/config/data_sources.yaml", "w") as f:
    f.write("""
primary: eastmoney
backup: tiantian
timeout: 30
retry: 3
""")

# Log files (distractors)
with open("workspace/logs/fetch_2024-01-10.log", "w") as f:
    f.write("2024-01-10 08:00:01 INFO Fetching fund data...\n")
    f.write("2024-01-10 08:00:05 INFO Done. 200 funds fetched.\n")

with open("workspace/logs/fetch_2024-01-11.log", "w") as f:
    f.write("2024-01-11 08:00:01 INFO Fetching fund data...\n")
    f.write("2024-01-11 08:00:07 WARNING Timeout on fund 003095\n")
    f.write("2024-01-11 08:00:08 INFO Retrying...\n")

# Notebook distractor
with open("workspace/notebooks/exploratory_analysis.py", "w") as f:
    f.write("# Exploratory analysis\nimport pandas as pd\n# TODO: add analysis\n")

# Test file (distractor)
with open("workspace/tests/test_screener.py", "w") as f:
    f.write("# Unit tests for screener\nimport subprocess\n# TODO\n")

# Utility distractor
with open("workspace/utils/helpers.py", "w") as f:
    f.write("""
def format_percent(val):
    return f'{val:.2f}%'

def fund_code_valid(code):
    return len(code) == 6 and code.isdigit()
""")

# Cache placeholder
with open("workspace/cache/.gitkeep", "w") as f:
    f.write("")

# Data raw distractor (malformed old NAV data)
with open("workspace/data/raw/nav_dump_legacy.csv", "w") as f:
    f.write("code,nav,date\n")
    f.write("110011,2.3450,2023-12-01\n")
    f.write("161039,1.2310,2023-12-01\n")
    f.write("003095,missing,2023-12-01\n")

# Processed data distractor
with open("workspace/data/processed/sample_holdings.json", "w") as f:
    json.dump({"note": "sample only", "holdings": []}, f, ensure_ascii=False)

# Extra distractor in scripts dir (unrelated script)
with open("workspace/scripts/data_cleanup.py", "w") as f:
    f.write("# Utility to clean old cache files\nimport os\n")

# README-like file but intentionally useless (no hints)
with open("workspace/config/notes.txt", "w") as f:
    f.write("Various configuration notes from 2023. Mostly outdated.\n")

print("Workspace generated successfully.")
print("Directory structure:")
for root, dirs_, files in os.walk("workspace"):
    level = root.replace("workspace", "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = " " * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")