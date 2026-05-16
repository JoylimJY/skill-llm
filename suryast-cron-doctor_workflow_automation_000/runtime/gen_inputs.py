#!/usr/bin/env python3
"""
Generate the sandbox workspace for the cron-doctor evaluation task.
Creates a realistic fintech environment with:
- A user crontab file
- System cron.d entries
- Messy syslog with cron output lines
- Distractor files
"""

import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/agent/workspace"))

# ── Directory structure ────────────────────────────────────────────────────────
dirs = [
    "scripts/trading",
    "scripts/backup",
    "scripts/security",
    "scripts/reports",
    "scripts/monitoring",
    "scripts/analytics",
    "logs/archive",
    "logs/app",
    "config/jobs",
    "config/env",
    "data/feeds",
    "data/exports",
    "reports",          # where the agent must write cron-health report
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractors = {
    "scripts/trading/sync_trades.sh": "#!/bin/bash\n# Sync trading positions from exchange API\nexport PYTHONPATH=/opt/fintech/lib\npython3 /opt/fintech/trading/sync.py --mode live\n",
    "scripts/trading/reconcile.sh": "#!/bin/bash\n# Daily reconciliation\npython3 /opt/fintech/trading/reconcile.py\n",
    "scripts/backup/db_backup.sh": "#!/bin/bash\n# PostgreSQL backup\npg_dump -U fintech fintech_prod > /var/backups/fintech_$(date +%Y%m%d).sql\ngzip /var/backups/fintech_$(date +%Y%m%d).sql\n",
    "scripts/backup/s3_sync.sh": "#!/bin/bash\naws s3 sync /var/backups s3://fintech-backups/\n",
    "scripts/security/audit_logins.sh": "#!/bin/bash\n# Audit failed logins\nlast -F | grep FAILED > /var/log/security/failed_logins.txt\n",
    "scripts/security/rotate_keys.sh": "#!/bin/bash\n# Rotate API keys\npython3 /opt/fintech/security/rotate.py\n",
    "scripts/reports/daily_pnl.sh": "#!/bin/bash\n# Send daily P&L to traders\npython3 /opt/fintech/reports/pnl.py --email traders@fintech.local\n",
    "scripts/monitoring/market_feed.sh": "#!/bin/bash\n# Monitor market data feed health\ncurl -sf http://feeds.internal/health || echo 'Feed down'\n",
    "scripts/analytics/weekly_cohort.sh": "#!/bin/bash\n# Weekly cohort analysis (nice-to-have)\npython3 /opt/fintech/analytics/cohort.py\n",
    "scripts/analytics/ad_hoc_dump.sh": "#!/bin/bash\n# Dump raw data for data science team\npython3 /opt/fintech/analytics/dump.py\n",
    "config/jobs/job_manifest.yaml": "# Job manifest (informational only)\njobs:\n  - sync_trades\n  - db_backup\n  - audit_logins\n",
    "config/env/prod.env": "DB_HOST=postgres.internal\nREDIS_HOST=redis.internal\nAPI_KEY=REDACTED\n",
    "data/feeds/symbols.csv": "AAPL,GOOGL,MSFT,TSLA,BTC,ETH\n",
    "logs/app/app.log": "[2024-06-10 01:00:12] INFO  Trading engine started\n[2024-06-10 01:00:14] INFO  Connected to exchange\n[2024-06-10 02:00:00] ERROR Connection timeout after 30s\n",
    "tmp/last_run.txt": "sync_trades: 2024-06-09 23:58:01\ndb_backup: 2024-06-09 00:05:12\n",
}
for rel, content in distractors.items():
    p = WORKSPACE / rel
    p.write_text(content)

# ── User crontab (/var/spool/cron/crontabs/agent or via crontab -l) ────────────
# We write to a file the agent should find by running crontab -l or by inspecting
# We'll install it as the agent's actual crontab AND write a raw copy for reference.
# Jobs:
#   1. sync_trades.sh       — every 5 min   — CRITICAL (trading)
#   2. db_backup.sh         — daily 1am     — CRITICAL (backup)
#   3. audit_logins.sh      — daily 2am     — CRITICAL (security)
#   4. daily_pnl.sh         — daily 7am     — HIGH (user-facing delivery)
#   5. market_feed.sh       — every 15 min  — MEDIUM (monitoring)
#   6. weekly_cohort.sh     — weekly Sun    — LOW (nice-to-have analytics)

USER_CRONTAB = """\
# Fintech batch jobs crontab
# m h  dom mon dow   command
*/5 * * * * /home/agent/workspace/scripts/trading/sync_trades.sh >> /tmp/sync_trades.log 2>&1
0 1 * * * /home/agent/workspace/scripts/backup/db_backup.sh >> /tmp/db_backup.log 2>&1
0 2 * * * /home/agent/workspace/scripts/security/audit_logins.sh >> /tmp/audit_logins.log 2>&1
0 7 * * * /home/agent/workspace/scripts/reports/daily_pnl.sh >> /tmp/daily_pnl.log 2>&1
*/15 * * * * /home/agent/workspace/scripts/monitoring/market_feed.sh >> /tmp/market_feed.log 2>&1
0 3 * * 0 /home/agent/workspace/scripts/analytics/weekly_cohort.sh >> /tmp/weekly_cohort.log 2>&1
"""
(WORKSPACE / "config/jobs/user_crontab.txt").write_text(USER_CRONTAB)

# Write crontab content to a temp file; setup.sh will install it to the proper
# spool directory (requires root permissions).
(WORKSPACE / "tmp/agent_crontab.txt").write_text(USER_CRONTAB)

# ── System cron.d entries ──────────────────────────────────────────────────────
CRON_D_ROTATE = """\
# /etc/cron.d/fintech-rotate-keys
# Rotate API keys nightly (security job)
30 2 * * * root /home/agent/workspace/scripts/security/rotate_keys.sh >> /tmp/rotate_keys.log 2>&1
"""
# Write to workspace; setup.sh (root) will copy to /etc/cron.d/
(WORKSPACE / "config/jobs/fintech-rotate-keys").write_text(CRON_D_ROTATE)

# ── Simulate /var/log/syslog with realistic cron entries ──────────────────────
# Today's date for the report filename
TODAY = datetime.now().strftime("%Y-%m-%d")
# Use a fixed "today" of 2024-06-10 for determinism
LOG_DATE = "Jun 10"

syslog_lines = []

def syslog_entry(time_str, job_name, pid, msg):
    return f"{LOG_DATE} {time_str} fintech-srv CRON[{pid}]: ({msg})"

def syslog_cmd(time_str, user, pid, cmd):
    return f"{LOG_DATE} {time_str} fintech-srv CRON[{pid}]: ({user}) CMD ({cmd})"

# ── sync_trades: fails with "command not found" (python3 not in cron PATH) ────
syslog_lines += [
    f"{LOG_DATE} 00:00:05 fintech-srv CRON[11201]: (agent) CMD (/home/agent/workspace/scripts/trading/sync_trades.sh >> /tmp/sync_trades.log 2>&1)",
    f"{LOG_DATE} 00:00:05 fintech-srv CRON[11202]: (CRON) error (grandchild #11202 failed with exit status 127)",
]
# Inject the command-not-found error into the job's own log
(WORKSPACE / "logs/archive/sync_trades_errors.log").write_text(
    f"{LOG_DATE} 00:00:05 /home/agent/workspace/scripts/trading/sync_trades.sh: line 3: python3: command not found\n"
    f"{LOG_DATE} 00:05:05 /home/agent/workspace/scripts/trading/sync_trades.sh: line 3: python3: command not found\n"
    f"{LOG_DATE} 00:10:05 /home/agent/workspace/scripts/trading/sync_trades.sh: line 3: python3: command not found\n"
)

# Also mirror into syslog
syslog_lines += [
    f"{LOG_DATE} 00:05:05 fintech-srv CRON[11210]: (agent) CMD (/home/agent/workspace/scripts/trading/sync_trades.sh >> /tmp/sync_trades.log 2>&1)",
    f"{LOG_DATE} 00:05:05 fintech-srv CRON[11211]: (CRON) error (grandchild #11211 failed with exit status 127)",
]

# ── db_backup: fails with "Permission denied" ──────────────────────────────────
syslog_lines += [
    f"{LOG_DATE} 01:00:01 fintech-srv CRON[12301]: (agent) CMD (/home/agent/workspace/scripts/backup/db_backup.sh >> /tmp/db_backup.log 2>&1)",
    f"{LOG_DATE} 01:00:01 fintech-srv CRON[12302]: (CRON) error (grandchild #12302 failed with exit status 1)",
]
(WORKSPACE / "logs/archive/db_backup_errors.log").write_text(
    f"{LOG_DATE} 01:00:01 pg_dump: error: connection to server on socket \"/var/run/postgresql/.s.PGSQL.5432\" failed: Permission denied\n"
)

# ── audit_logins: fails with "No such file or directory" ──────────────────────
syslog_lines += [
    f"{LOG_DATE} 02:00:01 fintech-srv CRON[13401]: (agent) CMD (/home/agent/workspace/scripts/security/audit_logins.sh >> /tmp/audit_logins.log 2>&1)",
    f"{LOG_DATE} 02:00:01 fintech-srv CRON[13402]: (CRON) error (grandchild #13402 failed with exit status 1)",
]
(WORKSPACE / "logs/archive/audit_logins_errors.log").write_text(
    f"{LOG_DATE} 02:00:01 /home/agent/workspace/scripts/security/audit_logins.sh: line 3: /var/log/security/failed_logins.txt: No such file or directory\n"
)

# ── rotate_keys (system cron.d): fails with "timeout" ─────────────────────────
syslog_lines += [
    f"{LOG_DATE} 02:30:01 fintech-srv CRON[14501]: (root) CMD (/home/agent/workspace/scripts/security/rotate_keys.sh >> /tmp/rotate_keys.log 2>&1)",
    f"{LOG_DATE} 02:30:01 fintech-srv CRON[14502]: (CRON) error (grandchild #14502 failed with exit status 124)",
]
(WORKSPACE / "logs/archive/rotate_keys_errors.log").write_text(
    f"{LOG_DATE} 02:30:01 timeout: /home/agent/workspace/scripts/security/rotate_keys.sh: job exceeded time limit (timeout after 60s)\n"
)

# ── daily_pnl: fails with "ECONNREFUSED" ──────────────────────────────────────
syslog_lines += [
    f"{LOG_DATE} 07:00:01 fintech-srv CRON[15601]: (agent) CMD (/home/agent/workspace/scripts/reports/daily_pnl.sh >> /tmp/daily_pnl.log 2>&1)",
    f"{LOG_DATE} 07:00:01 fintech-srv CRON[15602]: (CRON) error (grandchild #15602 failed with exit status 1)",
]
(WORKSPACE / "logs/archive/daily_pnl_errors.log").write_text(
    f"{LOG_DATE} 07:00:01 ConnectionRefusedError: [Errno 111] ECONNREFUSED – smtp.internal:587\n"
)

# ── market_feed: succeeds ──────────────────────────────────────────────────────
syslog_lines += [
    f"{LOG_DATE} 07:15:01 fintech-srv CRON[16701]: (agent) CMD (/home/agent/workspace/scripts/monitoring/market_feed.sh >> /tmp/market_feed.log 2>&1)",
    f"{LOG_DATE} 07:15:01 fintech-srv CRON[16701]: (agent) END (/home/agent/workspace/scripts/monitoring/market_feed.sh)",
    f"{LOG_DATE} 07:30:01 fintech-srv CRON[16801]: (agent) CMD (/home/agent/workspace/scripts/monitoring/market_feed.sh >> /tmp/market_feed.log 2>&1)",
    f"{LOG_DATE} 07:30:01 fintech-srv CRON[16801]: (agent) END (/home/agent/workspace/scripts/monitoring/market_feed.sh)",
]

# ── weekly_cohort: no recent run (missing output — job may not be running) ─────
# Intentionally absent from syslog

# ── Interleave some noisy unrelated syslog entries ────────────────────────────
noise = [
    f"{LOG_DATE} 01:05:33 fintech-srv systemd[1]: Started Daily apt upgrade and clean activities.",
    f"{LOG_DATE} 01:10:01 fintech-srv CRON[19001]: (root) CMD (  [ -x /usr/lib/php/sessionclean ] && if [ ! -d /run/systemd/system ]; then /usr/lib/php/sessionclean; fi)",
    f"{LOG_DATE} 03:00:01 fintech-srv CRON[19101]: (root) CMD (test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily ))",
    f"{LOG_DATE} 06:25:01 fintech-srv kernel: [1234567.890] eth0: renamed from veth3abc",
    f"{LOG_DATE} 07:17:22 fintech-srv sshd[20201]: Accepted publickey for agent",
]
# Merge and shuffle noise into syslog_lines at deterministic positions
all_lines = syslog_lines + noise
# Write syslog
syslog_path = Path("/var/log/syslog")
try:
    syslog_path.write_text("\n".join(all_lines) + "\n")
except PermissionError:
    # Write a local copy the agent can also find
    (WORKSPACE / "logs/syslog_snapshot.log").write_text("\n".join(all_lines) + "\n")

# Also create /tmp job logs with content matching errors
(Path("/tmp/sync_trades.log")).write_text(
    "/home/agent/workspace/scripts/trading/sync_trades.sh: line 3: python3: command not found\n" * 6
)
(Path("/tmp/db_backup.log")).write_text(
    "pg_dump: error: connection to server on socket \"/var/run/postgresql/.s.PGSQL.5432\" failed: Permission denied\n"
)
(Path("/tmp/audit_logins.log")).write_text(
    "/home/agent/workspace/scripts/security/audit_logins.sh: line 3: /var/log/security/failed_logins.txt: No such file or directory\n"
)
(Path("/tmp/rotate_keys.log")).write_text(
    "timeout: /home/agent/workspace/scripts/security/rotate_keys.sh: job exceeded time limit (timeout after 60s)\n"
)
(Path("/tmp/daily_pnl.log")).write_text(
    "ConnectionRefusedError: [Errno 111] ECONNREFUSED – smtp.internal:587\n"
)
(Path("/tmp/market_feed.log")).write_text("ok\nok\nok\n")

# Also write a readable copy of syslog in workspace logs in case /var/log/syslog is not accessible
(WORKSPACE / "logs/syslog_snapshot.log").write_text("\n".join(all_lines) + "\n")

print(f"Workspace generated at {WORKSPACE}")
print("Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")