import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── directory structure with distractors ──────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "logs",
    "config/backup",
    "data/raw",
    "data/processed",
    "reports/2025",
    "reports/2026",
    "tools/parsers",
    "tools/validators",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── realistic distractor files ────────────────────────────────────────────────

# 1. Old broken mcporter config (wrong format, stale)
old_cfg = {
    "version": "0.9.1",
    "servers": {
        "12306_legacy": {
            "endpoint": "http://old-12306-mcp.example.com",
            "timeout": 5000
        }
    }
}
with open(os.path.join(workspace, "config/backup/mcporter_old.json"), "w") as f:
    json.dump(old_cfg, f, indent=2)

# 2. Misleading station codes reference (contains errors)
bad_stations = """# Station Codes (DRAFT - DO NOT USE, contains errors)
City        | Code
-----------|------
成都东      | CDW    <- verify
西安北      | XAB    <- WRONG CODE, use ENH
上海        | SHA    <- incomplete
杭州        | HZH
"""
with open(os.path.join(workspace, "references/station-codes-draft.md"), "w") as f:
    f.write(bad_stations)

# 3. A confusing old query result (wrong format, different route)
old_result = [
    {"train": "G310", "from": "SHA", "to": "HZH", "depart": "09:00", "arrive": "10:30"},
    {"train": "D628", "from": "SHA", "to": "HZH", "depart": "11:00", "arrive": "12:45"},
]
with open(os.path.join(workspace, "data/raw/old_query_sha_hzh.json"), "w") as f:
    json.dump(old_result, f, indent=2)

# 4. A partial travel request document (business context)
travel_req = """Travel Request #TR-2026-0315
Requester: Zhang Wei (Corporate Travel Dept)
Date submitted: 2026-02-20

Route needed: Chengdu East → Xi'an North
Travel date: 2026-03-15
Preferred departure window: 08:00 – 14:00
Train type preference: High-speed or bullet trains only (no slow/ordinary trains)
Optimization goal: Minimize travel duration
Max results needed: Top 5 fastest options
Output format required: JSON file named train_options.json

Status: PENDING - awaiting ticket query execution
"""
with open(os.path.join(workspace, "data/raw/travel_request_TR2026_0315.txt"), "w") as f:
    f.write(travel_req)

# 5. Misleading query script (uses wrong parameters as a trap)
bad_script = """#!/bin/bash
# WARNING: This script is outdated and uses wrong parameters
mcporter call 12306.get-tickets \\
  date="2026-03-15" \\
  fromStation="CD" \\
  toStation="XA" \\
  trainFilterFlags="G" \\
  --config /etc/mcporter/config.json
"""
with open(os.path.join(workspace, "scripts/query-chengdu-xian-BROKEN.sh"), "w") as f:
    f.write(bad_script)

# 6. Correct mcporter.json config (agent must use this path)
mcporter_dir = os.path.expanduser("~/.mcporter")
os.makedirs(mcporter_dir, exist_ok=True)
mcporter_cfg = {
    "version": "1.1.0",
    "mcpServers": {
        "12306": {
            "command": "mock-12306-mcp",
            "args": [],
            "env": {}
        }
    }
}
with open(os.path.join(mcporter_dir, "mcporter.json"), "w") as f:
    json.dump(mcporter_cfg, f, indent=2)

# 7. Fake log files as distractors
for i in range(3):
    with open(os.path.join(workspace, f"logs/query_log_{2026010+i}.txt"), "w") as f:
        f.write(f"[2026-01-{10+i}] Query executed: SHH->HZH, result: 12 trains found\n")

# 8. Another distractor: partial CSV output from different tool
with open(os.path.join(workspace, "data/processed/tickets_export.csv"), "w") as f:
    f.write("train_no,from,to,depart,arrive,duration,seats\n")
    f.write("G2001,AOH,HZH,08:00,09:05,65min,有票\n")
    f.write("G2003,AOH,HZH,10:00,11:02,62min,有票\n")

# 9. Tools directory with unrelated validators
with open(os.path.join(workspace, "tools/validators/date_validator.py"), "w") as f:
    f.write("import re\ndef validate_date(d):\n    return bool(re.match(r'\\d{4}-\\d{2}-\\d{2}', d))\n")

with open(os.path.join(workspace, "tools/parsers/csv_parser.py"), "w") as f:
    f.write("import csv\ndef parse(path):\n    with open(path) as f:\n        return list(csv.DictReader(f))\n")

# 10. Reports directory with stale reports
with open(os.path.join(workspace, "reports/2025/annual_travel_summary.txt"), "w") as f:
    f.write("Total trips booked in 2025: 1,247\nMost common route: SHH-HZH\n")

with open(os.path.join(workspace, "reports/2026/q1_travel_budget.txt"), "w") as f:
    f.write("Q1 2026 Budget: CNY 450,000\nPriority routes: CDW-ENH, SHH-NKH\n")

# 11. Misleading README-like file in references (but no hints about the task)
with open(os.path.join(workspace, "references/railway-notes.md"), "w") as f:
    f.write("# Railway Notes\n\nSome general notes about Chinese railway system.\n\n"
            "- G trains are Gaotie (high-speed)\n"
            "- D trains are Dongche (EMU)\n"
            "- C trains are inter-city\n"
            "- Station codes vary by city/station\n")

print("Workspace initialized successfully.")
print(f"mcporter config written to: {mcporter_dir}/mcporter.json")