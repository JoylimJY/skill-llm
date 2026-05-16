import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ─── Directory structure ───────────────────────────────────────────────
dirs = [
    "ops/cron",
    "ops/logs",
    "ops/gateway",
    "scripts/deploy",
    "scripts/monitoring",
    "config/telegram",
    "config/models",
    "docs/runbooks",
    "docs/incidents",
    "archive/old-jobs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ─────────────────────────────────────────────────

# 1. Old broken cron job configuration (the "mess" to fix)
broken_jobs = [
    {
        "id": "job-001",
        "name": "morning-standup",
        "cron": "0 8 * * 1-5",
        "session": "main",               # BUG: should be isolated
        "message": "Good morning! Standup time.",  # BUG: no INSTRUCTION prefix
        "channel": "telegram",
        "to": "-1001234567890",
        "deliver": True,
        # BUG: missing --tz
        # BUG: missing --best-effort-deliver
        "status": "error",
        "last_error": "Message lost in active conversation",
    },
    {
        "id": "job-002",
        "name": "weekly-recap",
        "cron": "0 17 * * 5",
        "session": "main",               # BUG: should be isolated
        "message": "Weekly recap time!",  # BUG: no INSTRUCTION prefix
        "channel": "telegram",
        "to": "-1001234567890",
        "deliver": False,               # BUG: missing --deliver
        "status": "error",
        "last_error": "Delivery failed",
    },
]
with open(workspace / "ops/cron/broken_jobs.json", "w") as f:
    json.dump(broken_jobs, f, indent=2)

# 2. Gateway error log snippet
gateway_errors = """\
[2024-01-15 08:00:01] ERROR: cron tool deadlock detected, gateway timeout after 80s
[2024-01-15 08:00:01] ERROR: job-001 failed: message lost in main session
[2024-01-15 08:01:05] WARN:  UTC offset mismatch, expected America/La_Paz got UTC
[2024-01-15 09:00:00] ERROR: cron tool timed out after 10s
[2024-01-15 09:00:00] ERROR: job-002 failed: no delivery channel configured
[2024-01-15 10:15:22] ERROR: fallback model called exec tool unexpectedly
"""
with open(workspace / "ops/gateway/gateway.err.log", "w") as f:
    f.write(gateway_errors)

# 3. Incident report
incident_md = """\
# Incident Report: 2024-01-15

## Summary
Multiple cron jobs failed silently. Team missed standup notifications.

## Affected Jobs
- morning-standup (job-001): messages not delivered
- weekly-recap (job-002): no delivery at all

## Team timezone
All jobs should run for the Bolivia team.
Bolivia timezone: UTC-4 (no DST)

## Telegram Group
Group ID: -1001234567890

## Required Schedules
1. morning-standup: every weekday at 08:00 Bolivia time
2. one-shot reminder: 30 minutes from now (run once, then auto-delete)

## Notes
- Previous engineer used 'cron' tool directly - caused timeouts
- Session configuration was wrong
- Timezone was never set
- Fallback model went rogue and called tools it shouldn't
"""
with open(workspace / "docs/incidents/2024-01-15-cron-failure.md", "w") as f:
    f.write(incident_md)

# 4. Partial runbook (misleading / incomplete)
runbook = """\
# Cron Jobs Runbook (OUTDATED - DO NOT USE)

## Adding a job (old way)
cron add --name "job" --cron "* * * * *" --message "hello"

## Session types
Use --session main for most jobs.

## Delivery
Add --deliver if needed.

## Note: This runbook is outdated. Refer to SKILL.md for current best practices.
"""
with open(workspace / "docs/runbooks/cron-runbook-OUTDATED.md", "w") as f:
    f.write(runbook)

# 5. Distractor: deploy script
deploy_sh = """\
#!/bin/bash
# Deploy script - not related to cron
echo "Deploying application..."
docker-compose up -d
"""
with open(workspace / "scripts/deploy/deploy.sh", "w") as f:
    f.write(deploy_sh)

# 6. Distractor: monitoring config
monitoring_cfg = """\
[monitoring]
interval = 60
alert_threshold = 5
channels = telegram, slack
"""
with open(workspace / "scripts/monitoring/monitor.cfg", "w") as f:
    f.write(monitoring_cfg)

# 7. Distractor: telegram config (partial)
telegram_cfg = """\
{
  "bot_token": "REDACTED",
  "default_group": "-1001234567890",
  "fallback_group": "-1009876543210"
}
"""
with open(workspace / "config/telegram/telegram.json", "w") as f:
    f.write(telegram_cfg)

# 8. Distractor: model config
model_cfg = """\
primary_model: gpt-4o
fallback_model: gpt-3.5-turbo
timeout_seconds: 10
"""
with open(workspace / "config/models/models.yaml", "w") as f:
    f.write(model_cfg)

# 9. Distractor: archived old job
archived_job = """\
# Archived: old daily report job
# clawdbot cron add --name "old-report" --cron "0 18 * * *" --message "Report time" --session main
# Removed 2023-12-01 due to delivery failures
"""
with open(workspace / "archive/old-jobs/old-report.sh.bak", "w") as f:
    f.write(archived_job)

# 10. Distractor: ops notes
ops_notes = """\
Ops Notes
=========
- Gateway restarted 2024-01-10
- Bolivia team uses UTC-4 (America/La_Paz)
- Telegram group: -1001234567890
- Jobs keep failing - escalated to senior engineer
"""
with open(workspace / "ops/logs/ops-notes.txt", "w") as f:
    f.write(ops_notes)

# 11. Distractor: crontab (system, irrelevant)
crontab_txt = """\
# System crontab - not for clawdbot
0 2 * * * /usr/bin/logrotate /etc/logrotate.conf
*/5 * * * * /usr/local/bin/healthcheck.sh
"""
with open(workspace / "ops/cron/system-crontab.txt", "w") as f:
    f.write(crontab_txt)

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")