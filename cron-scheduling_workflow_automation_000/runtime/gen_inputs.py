import os
import random
import stat

random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure
dirs = [
    "pipeline/ingestion/raw",
    "pipeline/ingestion/validated",
    "pipeline/transform/daily",
    "pipeline/transform/quarterly",
    "pipeline/output/reports",
    "pipeline/output/archives",
    "ops/monitoring",
    "ops/alerts",
    "ops/locks",
    "config/env",
    "config/schedules",
    "logs/pipeline",
    "logs/audit",
    "scripts/helpers",
    "scripts/wrappers",
    "deploy/systemd",
    "deploy/cron",
    "data/trades",
    "data/positions",
    "data/risk",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Create distractor files (realistic but not the answer)
distractor_files = {
    "pipeline/ingestion/raw/trades_20240101.csv": "date,symbol,qty,price\n2024-01-01,AAPL,100,185.50\n",
    "pipeline/ingestion/validated/schema.json": '{"fields": ["date","symbol","qty","price"]}',
    "pipeline/transform/daily/transform.py": "#!/usr/bin/env python3\n# Transform daily trade data\nprint('transforming...')\n",
    "pipeline/transform/quarterly/aggregate.py": "#!/usr/bin/env python3\n# Aggregate quarterly positions\nprint('aggregating...')\n",
    "pipeline/output/reports/report_template.txt": "Q{quarter} Report\n=================\n",
    "ops/monitoring/check_health.sh": "#!/bin/bash\ncurl -s http://localhost:8080/health\n",
    "ops/alerts/notify.sh": "#!/bin/bash\necho 'ALERT: $1' >> /tmp/alerts.log\n",
    "config/env/prod.env": "DB_HOST=db.internal\nDB_PORT=5432\nDB_NAME=trades\n",
    "config/env/staging.env": "DB_HOST=staging-db.internal\nDB_PORT=5432\nDB_NAME=trades_staging\n",
    "config/schedules/old_cron_BROKEN.txt": (
        "# OLD BROKEN CRONTAB - DO NOT USE\n"
        "# Missing PATH, MAILTO\n"
        "5 * * * * /scripts/ingest.sh\n"  # wrong syntax example
        "0 2 * * * /scripts/backup.sh\n"
    ),
    "config/schedules/notes.txt": (
        "Jobs needed:\n"
        "- Ingest: every 15 min during market hours (Mon-Fri 9AM-5PM ET)\n"
        "- Daily report: 6:30 AM UTC weekdays\n"
        "- Quarterly cleanup: 1st of Jan/Apr/Jul/Oct at midnight UTC\n"
        "- On boot: run preflight checks\n"
        "- Timer-based: archive service, daily at 3AM, with up to 5min random delay\n"
        "NOTE: All schedules must be DST-safe (UTC). Ingest must not overlap itself.\n"
    ),
    "logs/pipeline/ingest.log": "[2024-01-15T09:00:01Z] START\n[2024-01-15T09:00:03Z] SUCCESS (2s)\n",
    "logs/audit/access.log": "2024-01-15 08:59:00 user=pipeline action=login\n",
    "scripts/helpers/db_connect.sh": "#!/bin/bash\npsql $DB_HOST -U pipeline\n",
    "scripts/helpers/validate.sh": "#!/bin/bash\necho 'Validating input...'\n",
    "data/trades/README_FORMAT.txt": "Columns: date, symbol, qty, price, venue\n",
    "data/positions/current.csv": "symbol,long,short\nAAPL,1000,200\n",
    "data/risk/limits.json": '{"max_position": 10000, "max_drawdown": 0.05}',
    "deploy/systemd/old_backup.service": (
        "[Unit]\nDescription=Old backup (DEPRECATED)\n\n"
        "[Service]\nType=oneshot\nExecStart=/bin/true\n"
    ),
    "deploy/cron/README.md": "Place new crontab entries in pipeline.crontab\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# Make shell scripts executable
for rel_path in distractor_files:
    if rel_path.endswith(".sh"):
        full_path = os.path.join(workspace, rel_path)
        st = os.stat(full_path)
        os.chmod(full_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# Create the actual target scripts that the cron/timer jobs will reference
# These must exist so the agent knows what to schedule

scripts = {
    "scripts/ingest.sh": (
        "#!/bin/bash\n"
        "# Market data ingestion script\n"
        "# Reads from data/trades/ and validates\n"
        "echo 'Ingesting market data...'\n"
        "sleep 1\n"
    ),
    "scripts/daily_report.sh": (
        "#!/bin/bash\n"
        "# Generate daily trading report\n"
        "echo 'Generating daily report...'\n"
        "sleep 2\n"
    ),
    "scripts/quarterly_cleanup.sh": (
        "#!/bin/bash\n"
        "# Quarterly data cleanup and archival\n"
        "echo 'Running quarterly cleanup...'\n"
        "sleep 3\n"
    ),
    "scripts/preflight.sh": (
        "#!/bin/bash\n"
        "# Pre-flight checks on system boot\n"
        "echo 'Running preflight checks...'\n"
    ),
    "scripts/archive.sh": (
        "#!/bin/bash\n"
        "# Archive pipeline outputs\n"
        "echo 'Archiving pipeline outputs...'\n"
        "sleep 5\n"
    ),
    "scripts/job_wrapper.sh": (
        "#!/bin/bash\n"
        "# Placeholder - agent must implement wrapper logic\n"
        "# Usage: job_wrapper.sh <job-name> <command> [args...]\n"
        "echo 'NOT IMPLEMENTED'\n"
        "exit 1\n"
    ),
}

for rel_path, content in scripts.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)
    st = os.stat(full_path)
    os.chmod(full_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

print("Workspace initialized successfully.")