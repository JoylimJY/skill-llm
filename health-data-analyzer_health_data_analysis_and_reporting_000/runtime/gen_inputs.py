import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "health_exports/raw/2025/Q4",
    "health_exports/raw/2026/Q1",
    "health_exports/processed/sleep",
    "health_exports/processed/workout",
    "health_exports/processed/recovery",
    "configs/mcp",
    "configs/devices",
    "logs/mcporter",
    "logs/server",
    "reports/archive/2025",
    "reports/archive/2026/january",
    "reports/archive/2026/february",
    "scripts/analysis",
    "scripts/export",
    "tmp/cache",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "health_exports/raw/2025/Q4/export_manifest.json": json.dumps({
        "version": "1.2", "exported_at": "2025-12-31T23:59:00Z",
        "tables": ["sleep_segments", "recovery_calculations"],
        "record_count": 1847
    }, indent=2),
    "health_exports/raw/2026/Q1/partial_export.csv": "date,metric,value\n2026-01-01,hrv,42.3\n2026-01-02,hrv,38.1\n",
    "health_exports/processed/sleep/sleep_summary_feb.txt": "February Sleep Summary\nAvg duration: 7h 12m\nAvg deep sleep: 1h 05m\nData quality: normal\n",
    "health_exports/processed/workout/workout_log_march.csv": "date,type,duration_min,calories\n2026-03-01,RUNNING,35,320\n2026-03-03,STRENGTH,45,280\n2026-03-05,HIIT,25,310\n",
    "health_exports/processed/recovery/recovery_notes.txt": "Week of Feb 22: Recovery trending low due to high training load\nWeek of Mar 1: Expect improvement\n",
    "configs/mcp/server_config.yaml": "server: healthdata\nhost: localhost\nport: 5400\ntimeout: 30\nretry: 3\n",
    "configs/devices/device_registry.json": json.dumps({
        "devices": [
            {"id": "dev_001", "name": "WHOOP 4.0", "platform": "appleHealth"},
            {"id": "dev_002", "name": "RingConn健康", "platform": "appleHealth"},
            {"id": "dev_003", "name": "华为运动健康", "platform": "appleHealth"}
        ]
    }, indent=2),
    "logs/mcporter/mcporter_2026-02-28.log": "[INFO] Connected to healthdata\n[INFO] query_table_data: sleep_segments rows=7\n[INFO] Disconnected\n",
    "logs/server/healthdata_server.log": "[2026-03-01 00:00:01] Server started\n[2026-03-01 00:05:22] Query: recovery_calculations\n[2026-03-07 23:59:00] 147 queries served\n",
    "reports/archive/2025/annual_health_report.json": json.dumps({
        "year": 2025,
        "avg_sleep_score": 74.2,
        "avg_recovery_score": 68.1,
        "total_workouts": 187,
        "note": "Archive only - do not use for current analysis"
    }, indent=2),
    "reports/archive/2026/january/jan_summary.json": json.dumps({
        "month": "2026-01",
        "avg_sleep_score": 71.8,
        "avg_recovery_score": 65.4,
        "sleep_debt_avg_minutes": -18.5
    }, indent=2),
    "reports/archive/2026/february/feb_summary.json": json.dumps({
        "month": "2026-02",
        "avg_sleep_score": 76.3,
        "avg_recovery_score": 70.2,
        "sleep_debt_avg_minutes": 12.1
    }, indent=2),
    "scripts/analysis/trend_analyzer.py": "# Placeholder trend analyzer\n# Usage: python trend_analyzer.py --input data.json --output report.json\nprint('Not implemented yet')\n",
    "scripts/export/export_to_csv.sh": "#!/bin/bash\n# Export health data to CSV\necho 'Export script - requires healthdata connection'\n",
    "tmp/cache/query_cache.json": json.dumps({
        "cached_at": "2026-02-28T12:00:00Z",
        "query": "sleep_segments",
        "rows": 14,
        "expired": True
    }, indent=2),
    "configs/mcp/mcporter_aliases.sh": "#!/bin/bash\nalias hd='mcporter call healthdata'\nalias hd-list='mcporter call healthdata.list_available_tables'\n",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace initialized with distractor files.")
print(f"Total distractor files: {len(distractor_files)}")