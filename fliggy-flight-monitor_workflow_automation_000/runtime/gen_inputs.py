import os
import json
from pathlib import Path

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create a realistic, deeply nested directory structure with distractor files

# --- Distractor: old travel booking records ---
old_records = workspace / "travel_records" / "2025"
old_records.mkdir(parents=True, exist_ok=True)

(old_records / "Q1_business_trips.csv").write_text(
    "employee,route,date,cost\nZhang Wei,BJS-SHA,2025-01-10,1200\nLi Fang,SHA-CTU,2025-02-14,980\n"
)
(old_records / "Q2_expense_report.xlsx.stub").write_text(
    "STUB: This file is a placeholder for the Q2 expense report\n"
)
(old_records / "travel_policy_v2.txt").write_text(
    "Travel Policy v2:\n- Economy class for flights under 4h\n- Business class allowed for international\n- Max per diem: 500 CNY\n"
)

# --- Distractor: old monitoring attempts (wrong format, wrong schema) ---
old_monitor = workspace / "monitor_configs" / "archive"
old_monitor.mkdir(parents=True, exist_ok=True)

# Wrong schema - missing required fields, wrong structure
(old_monitor / "beijing_sanya_old.json").write_text(json.dumps({
    "task": "monitor flight",
    "route": "BJS->SYX",
    "interval": "daily",
    "alert_price": 1500
}, indent=2))

# Another wrong attempt
(old_monitor / "hangzhou_xian_failed.json").write_text(json.dumps({
    "name": "flight monitor HGH SIA",
    "cron": "0 9 * * *",
    "message": "check price",
    "session": "new"
}, indent=2))

# --- Distractor: partial memory files (wrong path, wrong format) ---
wrong_memory = workspace / "data" / "flights"
wrong_memory.mkdir(parents=True, exist_ok=True)

(wrong_memory / "guangzhou_kunming.md").write_text(
    "# Flight Data\nRoute: CAN to KMG\nDate checked: 2026-01-15\nPrice: 450\n"
)
(wrong_memory / "shenzhen_tokyo_notes.txt").write_text(
    "Checked SZX to TYO on 2026-02-20. Price was 3200. Too expensive.\n"
)

# --- Distractor: city code reference (intentionally incomplete / wrong entries) ---
refs = workspace / "references"
refs.mkdir(parents=True, exist_ok=True)

(refs / "airport_codes_partial.txt").write_text(
    "# Partial Airport Code Reference (may be outdated)\n"
    "Beijing: PEK\n"
    "Shanghai: PVG\n"
    "Guangzhou: CAN\n"
    "Shenzhen: SZX\n"
    "Note: This list is incomplete. Do not use for bookings.\n"
)

(refs / "fliggy_api_notes.txt").write_text(
    "# Fliggy API Notes (DRAFT)\n"
    "Base URL: www.fliggy.com\n"
    "Note: Mobile and PC URLs differ. Use PC URL for stability.\n"
    "Parameters may vary by version.\n"
    "Last updated: 2025-06-01 - POSSIBLY OUTDATED\n"
)

# --- Distractor: unrelated cron examples ---
cron_examples = workspace / "automation" / "examples"
cron_examples.mkdir(parents=True, exist_ok=True)

(cron_examples / "weather_monitor.json").write_text(json.dumps({
    "name": "Weather Check",
    "schedule": {
        "kind": "interval",
        "every": "1h"
    },
    "payload": {
        "kind": "webhook",
        "url": "http://internal-api/weather"
    }
}, indent=2))

(cron_examples / "stock_alert.json").write_text(json.dumps({
    "name": "Stock Price Alert",
    "schedule": {
        "kind": "cron",
        "expr": "*/30 9-15 * * 1-5"
    },
    "payload": {
        "kind": "script",
        "script": "check_stocks.py"
    },
    "sessionTarget": "shared"
}, indent=2))

# --- Distractor: README for unrelated project ---
(workspace / "README_travel_system.txt").write_text(
    "Travel Management System v3\n"
    "============================\n"
    "This system manages corporate travel bookings.\n"
    "For flight monitoring, contact the IT team.\n"
    "Last updated: 2025-11-20\n"
)

# --- Distractor: logs directory ---
logs = workspace / "logs" / "monitoring"
logs.mkdir(parents=True, exist_ok=True)

(logs / "2026-03-01.log").write_text(
    "[2026-03-01 09:00:01] Monitoring task started\n"
    "[2026-03-01 09:00:15] Error: Invalid config schema\n"
    "[2026-03-01 09:00:15] Task aborted\n"
)
(logs / "2026-03-10.log").write_text(
    "[2026-03-10 09:00:01] Monitoring task started\n"
    "[2026-03-10 09:00:20] Warning: City code not found: 'XMN'\n"
    "[2026-03-10 09:00:20] Falling back to manual input\n"
)

# --- Distractor: a script directory ---
scripts = workspace / "scripts"
scripts.mkdir(parents=True, exist_ok=True)

(scripts / "fetch_prices.sh").write_text(
    "#!/bin/bash\n# Placeholder script - not functional\necho 'Price fetching not implemented'\nexit 1\n"
)
(scripts / "parse_snapshot.py").write_text(
    "# Placeholder - parse browser snapshot\n# TODO: implement parsing logic\nraise NotImplementedError('Not implemented')\n"
)

# --- The actual task context: A request brief left by the manager ---
(workspace / "task_brief.txt").write_text(
    "Task Brief - Corporate Travel Monitoring Setup\n"
    "==============================================\n"
    "Prepared by: Manager Wang\n"
    "Date: 2026-03-15\n\n"
    "We need to set up automated flight price monitoring for the following business travel:\n\n"
    "Route: Chengdu to Kunming\n"
    "Outbound date: April 10, 2026\n"
    "Return date: April 15, 2026\n"
    "(This is a ROUND-TRIP booking)\n\n"
    "Requirements:\n"
    "1. Monitor every 6 hours\n"
    "2. Alert threshold: 800 CNY\n"
    "3. Monitoring should start at 09:00 Shanghai time and repeat every 6 hours\n\n"
    "Deliverables needed:\n"
    "a) A monitoring task configuration file: flight_monitor_task.json\n"
    "b) An initial price tracking record initialized in the correct monitoring memory location\n"
    "c) The flight search URL for the round-trip query (write it to: search_url.txt)\n\n"
    "Please set this up according to our flight monitoring system documentation.\n"
)

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")
# Show structure
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")