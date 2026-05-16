import json
import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "logs/builds",
    "logs/deployments",
    "logs/security",
    "config/old",
    "config/archived",
    "metrics/daily",
    "metrics/weekly",
    "reports/q1",
    "reports/q2",
    "scripts/deprecated",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "logs/builds/build_001.log": (
        "[2024-06-01 02:15:00] Starting build pipeline\n"
        "[2024-06-01 02:15:45] Compiling assets...\n"
        "[2024-06-01 02:16:30] Build succeeded\n"
    ),
    "logs/builds/build_002.log": (
        "[2024-06-02 11:00:00] Starting build pipeline\n"
        "[2024-06-02 11:02:00] ERROR: missing STRIPE_KEY\n"
        "[2024-06-02 11:02:01] Build FAILED\n"
    ),
    "logs/deployments/deploy_v2.3.1.log": (
        "Deploy started: 2024-06-03 09:00:00 UTC\n"
        "Rolling update: 0/10 pods\n"
        "Rolling update: 5/10 pods\n"
        "Rolling update: 10/10 pods\n"
        "Deploy complete: 2024-06-03 09:07:33 UTC\n"
    ),
    "logs/security/audit_june.log": (
        "2024-06-01 00:00:00 - Auth scan started\n"
        "2024-06-01 00:01:13 - 0 critical findings\n"
        "2024-06-04 03:22:00 - CRITICAL: Unauthorized SSH login attempt from 185.220.101.42\n"
    ),
    "config/old/notification_config_v1.yaml": (
        "# Deprecated config - do not use\n"
        "channel: slack\n"
        "batching: false\n"
        "quiet_hours: none\n"
    ),
    "config/archived/alert_rules_2023.json": json.dumps({
        "rules": [
            {"type": "build_fail", "channel": "email"},
            {"type": "deploy_ok", "channel": "none"},
        ]
    }, indent=2),
    "metrics/daily/2024-06-03.csv": (
        "metric,value\n"
        "api_latency_p99,142ms\n"
        "error_rate,0.003\n"
        "active_users,8821\n"
    ),
    "metrics/weekly/week22.csv": (
        "week,deploys,failures,uptime_pct\n"
        "22,14,1,99.92\n"
    ),
    "reports/q1/summary.txt": (
        "Q1 2024 Platform Summary\n"
        "Total deployments: 52\n"
        "Mean time to recovery: 18 min\n"
        "Incidents: 3 (all resolved)\n"
    ),
    "reports/q2/draft_metrics.txt": (
        "Q2 Draft - incomplete\n"
        "Deployments so far: 31\n"
        "TODO: add cost breakdown\n"
    ),
    "scripts/deprecated/old_notifier.sh": (
        "#!/bin/bash\n"
        "# DEPRECATED - replaced by new notification skill\n"
        "curl -X POST https://hooks.slack.com/services/FAKE/WEBHOOK -d '{\"text\": \"$1\"}'\n"
    ),
    "config/old/escalation_v0.txt": (
        "Old escalation policy:\n"
        "- Try every 30 min until someone answers\n"
        "- CC the whole team immediately\n"
        "Note: this policy was revoked\n"
    ),
}

for rel_path, content in distractor_files.items():
    fp = workspace / rel_path
    fp.write_text(content)

# ── User Preferences ─────────────────────────────────────────────────────────
user_preferences = {
    "users": [
        {
            "id": "alice",
            "name": "Alice Romero",
            "primary_channel": "telegram",
            "critical_channel": "push",
            "timezone": "Europe/Madrid",
            "quiet_hours": {"start": "23:00", "end": "08:00"}
        },
        {
            "id": "bob",
            "name": "Bob Nakamura",
            "primary_channel": "email",
            "critical_channel": "push",
            "timezone": "Asia/Tokyo",
            "quiet_hours": {"start": "23:00", "end": "08:00"}
        },
        {
            "id": "carol",
            "name": "Carol Singh",
            "primary_channel": "slack",
            "critical_channel": "sms",
            "timezone": "America/New_York",
            "quiet_hours": {"start": "23:00", "end": "08:00"}
        }
    ]
}
(workspace / "user_preferences.json").write_text(json.dumps(user_preferences, indent=2))

# ── Incoming Events ──────────────────────────────────────────────────────────
# Designed to exercise ALL the proprietary traps:
#
#  E01 – security alert (level 5) at 03:22 local Alice time → MUST break quiet hours, push+chat immediately
#  E02 – build failed (level 4, deadline <2h) at 14:05 Madrid → immediate, telegram
#  E03 – deploy complete (level 2, task completed) project=alpha at 14:06 Madrid → batch candidate 1
#  E04 – deploy complete (level 2, task completed) project=alpha at 14:08 Madrid → batch candidate 2
#  E05 – deploy complete (level 2, task completed) project=alpha at 14:09 Madrid → batch candidate 3 → MUST batch E03+E04+E05
#  E06 – daily summary for Bob (informational level 1) at 02:00 Tokyo → quiet hours → queue to 08:00 Tokyo
#  E07 – debug/internal status → LOG ONLY, never notify
#  E08 – weekly summary for Carol at 09:00 NY → email, scheduled, confirmation block required
#  E09 – system down (level 5) for Carol at 23:30 NY → MUST break quiet hours, push+sms
#  E10 – task completed for Bob (level 2) at 00:30 Tokyo → quiet hours → queue to 08:00 Tokyo
#  E11 – critical alert for Alice that had no response (requires escalation plan)

incoming_events = {
    "events": [
        {
            "id": "E01",
            "type": "security_alert",
            "level": 5,
            "recipient": "alice",
            "project": "infra",
            "timestamp_utc": "2024-06-04T01:22:00Z",
            "local_time_recipient": "2024-06-04T03:22:00+02:00",
            "raw_message": "Unauthorized SSH login attempt detected from IP 185.220.101.42 on prod-bastion-01. Root login was attempted.",
            "requires_action": True
        },
        {
            "id": "E02",
            "type": "build_failed",
            "level": 4,
            "recipient": "alice",
            "project": "payments",
            "timestamp_utc": "2024-06-04T12:05:00Z",
            "local_time_recipient": "2024-06-04T14:05:00+02:00",
            "raw_message": "Build #447 failed. Missing environment variable STRIPE_KEY in production. Deployment blocked.",
            "requires_action": True
        },
        {
            "id": "E03",
            "type": "task_completed",
            "level": 2,
            "recipient": "alice",
            "project": "alpha",
            "timestamp_utc": "2024-06-04T12:06:00Z",
            "local_time_recipient": "2024-06-04T14:06:00+02:00",
            "raw_message": "Deploy alpha-service v1.0.0 completed successfully.",
            "requires_action": False
        },
        {
            "id": "E04",
            "type": "task_completed",
            "level": 2,
            "recipient": "alice",
            "project": "alpha",
            "timestamp_utc": "2024-06-04T12:08:00Z",
            "local_time_recipient": "2024-06-04T14:08:00+02:00",
            "raw_message": "Deploy alpha-worker v1.0.1 completed successfully.",
            "requires_action": False
        },
        {
            "id": "E05",
            "type": "task_completed",
            "level": 2,
            "recipient": "alice",
            "project": "alpha",
            "timestamp_utc": "2024-06-04T12:09:00Z",
            "local_time_recipient": "2024-06-04T14:09:00+02:00",
            "raw_message": "Deploy alpha-frontend v2.0.0 completed successfully.",
            "requires_action": False
        },
        {
            "id": "E06",
            "type": "daily_summary",
            "level": 1,
            "recipient": "bob",
            "project": "platform",
            "timestamp_utc": "2024-06-04T17:00:00Z",
            "local_time_recipient": "2024-06-05T02:00:00+09:00",
            "raw_message": "Daily summary for platform team: 3 deploys, 0 failures, uptime 99.98%.",
            "requires_action": False
        },
        {
            "id": "E07",
            "type": "debug_internal",
            "level": 1,
            "recipient": "bob",
            "project": "platform",
            "timestamp_utc": "2024-06-04T12:30:00Z",
            "local_time_recipient": "2024-06-04T21:30:00+09:00",
            "raw_message": "Internal health-check: DB connection pool at 42/100. No anomalies detected.",
            "requires_action": False
        },
        {
            "id": "E08",
            "type": "weekly_summary",
            "level": 1,
            "recipient": "carol",
            "project": "platform",
            "timestamp_utc": "2024-06-10T13:00:00Z",
            "local_time_recipient": "2024-06-10T09:00:00-04:00",
            "raw_message": "Weekly platform summary for week 23: 14 deployments, 1 incident (resolved), uptime 99.92%.",
            "requires_action": False
        },
        {
            "id": "E09",
            "type": "system_down",
            "level": 5,
            "recipient": "carol",
            "project": "payments",
            "timestamp_utc": "2024-06-05T03:30:00Z",
            "local_time_recipient": "2024-06-04T23:30:00-04:00",
            "raw_message": "CRITICAL: payments-api is DOWN. All transactions failing. 100% error rate on /v1/charge endpoint.",
            "requires_action": True
        },
        {
            "id": "E10",
            "type": "task_completed",
            "level": 2,
            "recipient": "bob",
            "project": "reporting",
            "timestamp_utc": "2024-06-04T15:30:00Z",
            "local_time_recipient": "2024-06-05T00:30:00+09:00",
            "raw_message": "Weekly report generation for Q2 completed. File available at reports/q2/week23.pdf.",
            "requires_action": False
        },
        {
            "id": "E11",
            "type": "security_alert",
            "level": 5,
            "recipient": "alice",
            "project": "infra",
            "timestamp_utc": "2024-06-04T06:00:00Z",
            "local_time_recipient": "2024-06-04T08:00:00+02:00",
            "raw_message": "Critical: SSL certificate for api.company.com expires in 2 hours. Renewal failed twice. Manual intervention required.",
            "requires_action": True,
            "escalation_note": "First alert sent at 08:00 local. No response received. Escalation required."
        }
    ]
}
(workspace / "incoming_events.json").write_text(json.dumps(incoming_events, indent=2))

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")