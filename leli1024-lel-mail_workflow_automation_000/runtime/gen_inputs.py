import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

# ---------- workspace root ----------
WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ---------- distractor directory tree ----------
distractor_dirs = [
    "projects/quant/models",
    "projects/quant/backtests",
    "projects/risk/reports",
    "projects/risk/alerts",
    "projects/ops/monitoring",
    "projects/ops/cron",
    "logs/2024/q1",
    "logs/2024/q2",
    "config/legacy",
    "config/staging",
    "data/feeds/fx",
    "data/feeds/equity",
    "docs/runbooks",
]

for d in distractor_dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files (realistic but irrelevant)
distractor_files = {
    "projects/quant/models/pricing_model_v3.py": "# Black-Scholes pricing model\nimport math\ndef bs_price(S,K,T,r,sigma): pass\n",
    "projects/quant/backtests/backtest_2024Q1.csv": "date,pnl,sharpe\n2024-01-01,1200.5,1.4\n2024-01-02,-340.2,1.3\n",
    "projects/risk/reports/var_report_march.json": json.dumps({"date":"2024-03-31","var_95":152000,"var_99":241000}),
    "projects/risk/alerts/alert_template.txt": "RISK ALERT: {instrument} breached {threshold} at {time}\n",
    "projects/ops/monitoring/health_check.sh": "#!/bin/bash\necho 'All systems nominal'\n",
    "projects/ops/cron/old_cron_entries.txt": "*/10 * * * * /usr/local/bin/feed_monitor.sh\n",
    "logs/2024/q1/system.log": "2024-01-15 09:32:11 INFO Feed connected\n2024-01-15 09:32:12 INFO Pricing engine started\n",
    "logs/2024/q2/system.log": "2024-04-01 08:00:01 INFO System restart\n2024-04-01 08:00:05 WARN Latency spike detected\n",
    "config/legacy/smtp_old.conf": "server=mail.legacy.corp.com\nport=25\nuser=ops@legacy.corp.com\n",
    "config/staging/db_config.json": json.dumps({"host":"staging-db.internal","port":5432,"db":"quant_staging"}),
    "data/feeds/fx/eurusd_2024.csv": "timestamp,bid,ask\n2024-01-02T08:00:00Z,1.0941,1.0943\n",
    "data/feeds/equity/spy_ticks.csv": "timestamp,price,volume\n2024-01-02T09:30:00Z,476.23,12000\n",
    "docs/runbooks/incident_response.md": "# Incident Response\n1. Page on-call\n2. Assess severity\n3. Escalate if P1\n",
}

for rel_path, content in distractor_files.items():
    p = WORKSPACE / rel_path
    p.write_text(content)

# ---------- SKILL SCRIPTS (mock implementations) ----------
# These are the scripts that SKILL.md says already exist.
# We place them at the paths SKILL.md references.

SKILL_BASE = Path.home() / ".openclaw/workspace/skills/lel-mail/scripts"
SKILL_BASE.mkdir(parents=True, exist_ok=True)

QUEUE_DIR = Path.home() / ".openclaw/workspace/skills/lel-mail/queue"
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

SENT_LOG = Path.home() / ".openclaw/workspace/skills/lel-mail/sent.log"
SENT_LOG.write_text("")  # empty initially

# ---- Pre-populate the queue with two existing emails ----
# Email #1: a stale draft that must be deleted per the task
queued_email_1 = {
    "id": "QM-20240415-001",
    "sender": "risk-alerts@tradingdesk.com",
    "recipient": "cto@tradingdesk.com",
    "subject": "DRAFT: VaR limit breach - DO NOT SEND",
    "body": "This is an erroneous draft that was queued by mistake. Please disregard.",
    "cc": "",
    "bcc": "",
    "queued_at": "2024-04-15T07:12:00Z"
}
# Email #2: a legitimate queued email (should remain)
queued_email_2 = {
    "id": "QM-20240415-002",
    "sender": "risk-alerts@tradingdesk.com",
    "recipient": "compliance@tradingdesk.com",
    "subject": "Daily VaR Summary",
    "body": "Please find attached the daily VaR summary for 15-Apr-2024.",
    "cc": "",
    "bcc": "",
    "queued_at": "2024-04-15T07:45:00Z"
}

(QUEUE_DIR / "QM-20240415-001.json").write_text(json.dumps(queued_email_1, indent=2))
(QUEUE_DIR / "QM-20240415-002.json").write_text(json.dumps(queued_email_2, indent=2))

# ---- Mock check_email.sh ----
check_email_sh = r"""#!/bin/bash
# Mock check_email.sh <USER_EMAIL>
EMAIL=$1
if [ -z "$EMAIL" ]; then
    echo "Usage: check_email.sh <USER_EMAIL>"
    exit 1
fi
echo "Checking inbox for: $EMAIL"
echo "No new messages."
exit 0
"""
(SKILL_BASE / "check_email.sh").write_text(check_email_sh)

# ---- Mock email_send.sh ----
email_send_sh = r"""#!/bin/bash
# Mock email_send.sh
# Parses flags: --sender --recipient --subject --body [--cc] [--bcc]
SENDER=""
RECIPIENT=""
SUBJECT=""
BODY=""
CC=""
BCC=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --sender)   SENDER="$2";    shift 2 ;;
        --recipient) RECIPIENT="$2"; shift 2 ;;
        --subject)  SUBJECT="$2";   shift 2 ;;
        --body)     BODY="$2";      shift 2 ;;
        --cc)       CC="$2";        shift 2 ;;
        --bcc)      BCC="$2";       shift 2 ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

if [ -z "$SENDER" ] || [ -z "$RECIPIENT" ] || [ -z "$BODY" ]; then
    echo "ERROR: --sender, --recipient, and --body are required."
    exit 1
fi

QUEUE_DIR="$HOME/.openclaw/workspace/skills/lel-mail/queue"
TIMESTAMP=$(date -u +"%Y%m%d%H%M%S%N")
ID="QM-SENT-${TIMESTAMP}"
OUTFILE="${QUEUE_DIR}/${ID}.json"

python3 - <<PYEOF
import json, os
data = {
    "id": "${ID}",
    "sender": "${SENDER}",
    "recipient": "${RECIPIENT}",
    "subject": "${SUBJECT}",
    "body": """${BODY}""",
    "cc": "${CC}",
    "bcc": "${BCC}",
    "queued_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
with open("${OUTFILE}", "w") as f:
    json.dump(data, f, indent=2)
print(f"Queued email with ID: ${ID}")
PYEOF
"""
(SKILL_BASE / "email_send.sh").write_text(email_send_sh)

# ---- Mock manage_queue.py ----
manage_queue_py = r"""#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

QUEUE_DIR = Path.home() / ".openclaw/workspace/skills/lel-mail/queue"

def list_queue():
    files = sorted(QUEUE_DIR.glob("*.json"))
    if not files:
        print("Queue is empty.")
        return
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
        print(f"ID: {data['id']}")
        print(f"  From:    {data.get('sender','')}")
        print(f"  To:      {data.get('recipient','')}")
        print(f"  Subject: {data.get('subject','')}")
        print(f"  Queued:  {data.get('queued_at','')}")
        print()

def delete_email(email_id):
    found = False
    for f in QUEUE_DIR.glob("*.json"):
        with open(f) as fh:
            data = json.load(fh)
        if data.get("id") == email_id:
            os.remove(f)
            print(f"Deleted email ID: {email_id}")
            found = True
            break
    if not found:
        print(f"No email found with ID: {email_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--delete", type=str)
    args = parser.parse_args()

    if args.list:
        list_queue()
    elif args.delete:
        delete_email(args.delete)
    else:
        parser.print_help()
"""
(SKILL_BASE / "manage_queue.py").write_text(manage_queue_py)

# ---- Mock email_sender_daemon.sh ----
daemon_sh = r"""#!/bin/bash
# Mock daemon - processes queue
QUEUE_DIR="$HOME/.openclaw/workspace/skills/lel-mail/queue"
SENT_LOG="$HOME/.openclaw/workspace/skills/lel-mail/sent.log"
for f in "$QUEUE_DIR"/*.json; do
    [ -f "$f" ] || continue
    echo "Sending: $f" >> "$SENT_LOG"
    rm "$f"
done
"""
(SKILL_BASE / "email_sender_daemon.sh").write_text(daemon_sh)

# ---- Make all scripts executable ----
for script in SKILL_BASE.iterdir():
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# ---------- Task briefing file in workspace ----------
task_brief = """# Quant Desk Automated Alert System - Setup Brief

## Context
Our risk management pipeline needs its automated email notification system configured
and operational. A VaR (Value at Risk) breach was detected this morning and we need
to dispatch an urgent alert.

## Key Contacts
- Risk Desk Lead: riskdesk@tradingdesk.com
- CRO (Chief Risk Officer): cro@tradingdesk.com
- Quant Team Lead: quantlead@tradingdesk.com  [CC on all risk alerts]
- Compliance Officer: compliance@tradingdesk.com  [CC on all risk alerts]

## Alert System Email Account
- Provider: gmail
- Account: risk-alerts@tradingdesk.com
- App Password: mock mock mock mock
- This account both sends and receives

## Pending Actions
1. The alert system config is not yet set up
2. There is a mistakenly queued draft (subject contains "DO NOT SEND") that must be retracted before it goes out
3. Send a new priority VaR breach alert email
"""
(WORKSPACE / "task_brief.md").write_text(task_brief)

print("Workspace setup complete.")
print(f"Skill scripts: {SKILL_BASE}")
print(f"Queue directory: {QUEUE_DIR}")