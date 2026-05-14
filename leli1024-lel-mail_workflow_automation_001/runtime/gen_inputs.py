#!/usr/bin/env python3
import os
import json
import random
import time
from pathlib import Path

random.seed(42)

workspace = Path("/root/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create deeply nested distractor structure ---
dirs = [
    "workspace/projects/fintech/compliance/q4_reports",
    "workspace/projects/fintech/compliance/audit_logs",
    "workspace/projects/fintech/ops/incidents",
    "workspace/projects/fintech/ops/runbooks",
    "workspace/projects/fintech/legal/contracts",
    "workspace/projects/fintech/legal/notifications",
    "workspace/communications/drafts",
    "workspace/communications/sent_archive",
    "workspace/communications/templates",
    "workspace/config/old_configs",
    "workspace/config/backups",
    "workspace/logs/system",
    "workspace/logs/app",
]
for d in dirs:
    Path(f"/root/{d}").mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = [
    ("workspace/projects/fintech/compliance/q4_reports/q4_summary.txt", "Q4 2024 Compliance Summary\nAll controls passed.\nAudit date: 2024-12-01\n"),
    ("workspace/projects/fintech/compliance/audit_logs/audit_2024_11.csv", "timestamp,event,user\n2024-11-01,login,alice\n2024-11-02,export,bob\n"),
    ("workspace/projects/fintech/ops/incidents/INC-2024-089.txt", "Incident: Payment gateway timeout\nStatus: Resolved\nImpact: Low\n"),
    ("workspace/projects/fintech/ops/runbooks/deploy_procedure.md", "# Deploy Procedure\n1. Run tests\n2. Tag release\n3. Deploy to prod\n"),
    ("workspace/projects/fintech/legal/contracts/vendor_agreement_v3.txt", "Vendor Agreement v3\nEffective: 2024-01-01\nParties: FinCorp, VendorX\n"),
    ("workspace/projects/fintech/legal/notifications/prior_notice_2024_09.txt", "Regulatory Notice\nDate: 2024-09-15\nSubject: GDPR Compliance Update\n"),
    ("workspace/communications/drafts/draft_ops_update.txt", "Hi team, please review the attached ops update...\n"),
    ("workspace/communications/templates/regulatory_notification.txt", "Template: Regulatory Notification\nDear [RECIPIENT],\nPlease be advised that...\n"),
    ("workspace/config/old_configs/smtp_legacy.json", '{"server": "smtp.legacy.internal", "port": 25}\n'),
    ("workspace/config/backups/config_backup_2024.json", '{"provider": "legacy", "auth": {"user": "old@corp.com"}}\n'),
    ("workspace/logs/system/syslog_2024_12.txt", "Dec 01 10:00:01 kernel: system boot\nDec 01 10:00:05 sshd: started\n"),
    ("workspace/logs/app/app_errors_2024_12.txt", "ERROR 2024-12-01 connection refused smtp.internal\nWARN  2024-12-01 retry attempt 3\n"),
]

for rel_path, content in distractor_files:
    p = Path(f"/root/{rel_path}")
    p.write_text(content)

# --- Create the lel-mail skill directory structure ---
skill_scripts_dir = Path("/root/.openclaw/workspace/skills/lel-mail/scripts")
skill_scripts_dir.mkdir(parents=True, exist_ok=True)

# --- Create the lel-mail config directory ---
config_dir = Path("/root/.config/lel-mail")
config_dir.mkdir(parents=True, exist_ok=True)

# Write a valid config file
config = [
    {
        "provider": "gmail",
        "config": {
            "smtp": {"server": "smtp.gmail.com", "port": 587},
            "imap": {"server": "imap.gmail.com", "port": 993}
        },
        "auth": {
            "user": "compliance@fincorp.com",
            "password": "xxxx xxxx xxxx xxxx"
        },
        "can_send": True,
        "can_read": True
    }
]
with open(config_dir / "config.json", "w") as f:
    json.dump(config, f, indent=2)

# --- Create the queue directory ---
queue_dir = Path("/root/.openclaw/workspace/skills/lel-mail/queue")
queue_dir.mkdir(parents=True, exist_ok=True)

# Pre-populate the queue with TWO stale emails (one is the "mistake" that needs deleting)
# Email 1 - stale accidental email (should be deleted)
stale_email_id = "a3f9b1c2"
stale_email = {
    "id": stale_email_id,
    "sender": "compliance@fincorp.com",
    "recipient": "all-staff@fincorp.com",
    "subject": "TEST - ignore this",
    "body": "This was sent by accident during a test. Please disregard.",
    "cc": "",
    "bcc": "",
    "queued_at": "2024-12-10T08:30:00"
}
with open(queue_dir / f"{stale_email_id}.json", "w") as f:
    json.dump(stale_email, f, indent=2)

# Email 2 - another legitimate queued email (should NOT be deleted)
legit_email_id = "d7e2a0f4"
legit_email = {
    "id": legit_email_id,
    "sender": "compliance@fincorp.com",
    "recipient": "ops-lead@fincorp.com",
    "subject": "Monthly Ops Review",
    "body": "Please review the attached monthly ops summary.",
    "cc": "",
    "bcc": "",
    "queued_at": "2024-12-10T09:00:00"
}
with open(queue_dir / f"{legit_email_id}.json", "w") as f:
    json.dump(legit_email, f, indent=2)

# --- Write the task briefing file (business context, no hints) ---
task_brief = """\
COMPLIANCE NOTIFICATION - ACTION REQUIRED
==========================================
From: Sarah Chen, Chief Compliance Officer
To: AI Assistant

We need to send our Q4 regulatory notification email immediately.

Details:
  From: compliance@fincorp.com
  To: regulators@finra.org
  Subject: Q4 2024 Regulatory Compliance Notification
  Body: Please find attached our Q4 2024 compliance report. All regulatory requirements have been met. Contact compliance@fincorp.com for queries.
  BCC: legal@fincorp.com, audit@fincorp.com

Also - I just noticed there's an email in the outgoing queue with the subject "TEST - ignore this" 
that was queued by mistake. Please remove it before it goes out.

The legitimate "Monthly Ops Review" email should remain in the queue untouched.
"""
Path("/root/workspace/TASK_BRIEF.txt").write_text(task_brief)

print("Input generation complete.")
print(f"Queue pre-populated with IDs: {stale_email_id} (delete this), {legit_email_id} (keep this)")