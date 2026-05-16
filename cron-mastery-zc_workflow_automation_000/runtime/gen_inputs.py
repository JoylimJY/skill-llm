import json
import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# Directory structure
dirs = [
    "gateway/config",
    "gateway/state/cron",
    "gateway/logs",
    "services/reminder",
    "services/maintenance",
    "services/billing",
    "docs/legacy",
    "docs/archive",
    "scripts/migration",
    "scripts/cleanup",
    "monitoring/alerts",
    "monitoring/dashboards",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractors = [
    ("gateway/config/gateway.yaml", "heartbeat_interval: 30s\nmax_jobs: 500\nlog_level: info\n"),
    ("gateway/config/channels.yaml", "telegram:\n  bot_token: REDACTED\n  default_chat: 1027899060\nwhatsapp:\n  enabled: false\n"),
    ("gateway/logs/gateway_2026-01-01.log", "[INFO] Gateway started\n[INFO] Heartbeat: 30s\n[WARN] Legacy job detected: job_001\n[WARN] Legacy job detected: job_002\n"),
    ("gateway/logs/gateway_2026-01-02.log", "[INFO] 3 jobs loaded\n[ERROR] job_003: nextRunAtMs corrupted\n[INFO] Attempting repair...\n"),
    ("services/billing/invoice_scheduler.json", json.dumps({"name": "Monthly Invoice", "schedule": {"kind": "every", "everyMs": 2592000000}, "payload": {"kind": "systemEvent", "text": "[BILLING] Generate invoices"}, "sessionTarget": "main"}, indent=2)),
    ("services/billing/README_IGNORE.txt", "DO NOT MODIFY billing scheduler without approval from finance team.\n"),
    ("docs/legacy/migration_notes_2025.txt", "Migrated 12 jobs from v2025.x to v2026.1. Issues: atMs field deprecated. See changelog.\n"),
    ("docs/archive/old_cron_format.txt", "DEPRECATED: atMs field was used in pre-2026.2.3. All new jobs must use ISO 8601 'at' field.\n"),
    ("scripts/cleanup/purge_old_logs.sh", "#!/bin/bash\nfind /workspace/gateway/logs -mtime +30 -delete\necho 'Old logs purged'\n"),
    ("scripts/migration/check_legacy.py", "import json, sys\nwith open(sys.argv[1]) as f:\n    job = json.load(f)\nif 'atMs' in job.get('schedule', {}):\n    print('LEGACY FORMAT DETECTED')\nelse:\n    print('OK')\n"),
    ("monitoring/alerts/cpu_alert.json", json.dumps({"name": "CPU Alert", "threshold": 90, "channel": "telegram", "to": "1027899060"}, indent=2)),
    ("monitoring/dashboards/health.json", json.dumps({"dashboards": ["system_health", "job_queue", "delivery_stats"]}, indent=2)),
]

for path, content in distractors:
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# ── PROBLEM FILES ────────────────────────────────────────────────────────────
# TWO legacy cron job configs that need to be migrated to modern format.
# Both use pre-2026.2.3 patterns.

# Legacy Job 1: One-shot medication reminder (push notification)
# Issues: uses atMs (not ISO), deliver:true in payload, sessionTarget:"main" (should be isolated), missing deleteAfterRun, missing wakeMode, missing delivery object, missing agentTurn strict prompt
legacy_job_1 = {
    "name": "Remind: Take Metformin",
    "schedule": {
        "kind": "at",
        "atMs": 1738806600000  # 2026-02-06T01:30:00Z in ms
    },
    "payload": {
        "kind": "agentTurn",
        "message": "Time to take your Metformin, patient #4821!",
        "deliver": True
    },
    "sessionTarget": "main",
    "wakeMode": "lazy"
}

# Legacy Job 2: One-shot appointment reminder (push notification)
# Issues: uses atMs, deliver:true, sessionTarget:"main", no deleteAfterRun, wakeMode missing, no delivery block, no strict instruction prefix
legacy_job_2 = {
    "name": "Remind: Cardiology Appointment",
    "schedule": {
        "kind": "at",
        "atMs": 1738854000000  # 2026-02-06T14:40:00Z in ms
    },
    "payload": {
        "kind": "agentTurn",
        "message": "Your cardiology appointment is in 30 minutes. Please prepare.",
        "deliver": True
    },
    "sessionTarget": "main",
    "wakeMode": "lazy"
}

with open(os.path.join(WORKSPACE, "services/reminder/legacy_job_med_reminder.json"), "w") as f:
    json.dump(legacy_job_1, f, indent=2)

with open(os.path.join(WORKSPACE, "services/reminder/legacy_job_appt_reminder.json"), "w") as f:
    json.dump(legacy_job_2, f, indent=2)

# Specification file: what the two NEW jobs should be
# (this gives business context without revealing the correct JSON structure)
new_job_spec = """PENDING AUTOMATION TASKS - MedTrack Platform
=============================================

Task A: PUSH NOTIFICATION — Daily Hydration Reminder
  Target patient: Momo (Telegram ID: 1027899060)
  Schedule: Daily at 09:00 AM Cairo time (GMT+2), i.e., 07:00 UTC
  Message to deliver verbatim: "💧 Drink water, Momo! Stay hydrated for your treatment."
  Requirement: Must wake agent proactively to deliver. Must not fire more than once per trigger.
  Output file: new_hydration_reminder.json

Task B: BACKGROUND MAINTENANCE — Nightly System Health Log
  Schedule: Every 24 hours (recurring)
  Purpose: Silent background log entry — do NOT alert users, just inject a status text into chat history.
  Log text: "[MAINTENANCE] MedTrack gateway health check passed."
  Requirement: Must be executed by the main session agent (full tool access needed for cleanup).
  Output file: new_maintenance_job.json
"""

with open(os.path.join(WORKSPACE, "services/maintenance/PENDING_TASKS.txt"), "w") as f:
    f.write(new_job_spec)

# Also write a context note about the legacy migration
migration_spec = """MIGRATION REQUEST — services/reminder/
======================================
The following two job config files are in the OLD pre-2026.2.3 format and must be
upgraded to the current standard (2026.2.15+):

  - legacy_job_med_reminder.json
  - legacy_job_appt_reminder.json

Both are push-notification reminders that must wake an agent proactively.
Both must be upgraded IN PLACE (same filenames, same directory).

Telegram delivery channel: to user ID 1027899060.

NOTE: atMs timestamps map to:
  - legacy_job_med_reminder.json  → 2026-02-06T01:30:00Z
  - legacy_job_appt_reminder.json → 2026-02-06T14:40:00Z
"""

with open(os.path.join(WORKSPACE, "scripts/migration/MIGRATION_REQUEST.txt"), "w") as f:
    f.write(migration_spec)

print("Workspace generated successfully.")