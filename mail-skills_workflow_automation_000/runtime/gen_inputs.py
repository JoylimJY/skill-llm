#!/usr/bin/env python3
"""
Generate the sandbox workspace for the mail-skill compliance audit task.
Creates a realistic directory structure with distractor files, a functional
mock mail_cli.py, and a pre-seeded SQLite database with compliance emails.
"""
import os
import json
import sqlite3
import random
import hashlib
import time
from pathlib import Path
from datetime import datetime, timedelta

SEED = 42
random.seed(SEED)

WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

def makedirs(*paths):
    for p in paths:
        (WORKSPACE / p).mkdir(parents=True, exist_ok=True)

# ── Directory skeleton ────────────────────────────────────────────────────────
makedirs(
    "scripts",
    "data/emails/raw",
    "data/emails/attachments",
    "data/exports",
    "data/archives",
    "logs",
    "config",
    "reports/quarterly",
    "reports/drafts",
    "tools/converters",
    "tools/validators",
    "tmp",
)

# ── Distractor files ──────────────────────────────────────────────────────────
distractor_files = {
    "config/smtp_config.yaml": "host: mail.example.com\nport: 587\ntls: true\n",
    "config/imap_config.yaml": "host: imap.example.com\nport: 993\nssl: true\n",
    "logs/mail_sync.log": "2024-01-15 08:00:01 INFO Sync started\n2024-01-15 08:01:22 INFO Sync completed: 42 emails\n",
    "logs/errors.log": "2024-01-10 12:34:56 ERROR Connection timeout to imap.example.com\n",
    "data/archives/backup_2023.tar.gz.stub": "# placeholder for archive\n",
    "data/exports/old_export_2023.csv": "id,subject,sender,date\n1,Old email,old@example.com,2023-01-01\n",
    "reports/quarterly/Q4_2023_summary.md": "# Q4 2023 Email Summary\n\nTotal emails processed: 1,203\n",
    "reports/drafts/draft_compliance_report.txt": "Draft: Pending review by legal team.\n",
    "tools/converters/eml_to_pdf.py": "# Stub: not implemented\n",
    "tools/validators/email_validator.py": "import re\ndef validate(email): return bool(re.match(r'[^@]+@[^@]+', email))\n",
    "tmp/session_cache.json": json.dumps({"last_sync": "2024-01-14T09:00:00", "account": "compliance@finfirm.com"}),
    ".env": (
        "MAIL_ACCOUNT_1_EMAIL=compliance_audit@finfirm.com\n"
        "MAIL_ACCOUNT_1_IMAP_HOST=127.0.0.1\n"
        "MAIL_ACCOUNT_1_IMAP_PORT=1430\n"
        "MAIL_ACCOUNT_1_SMTP_HOST=127.0.0.1\n"
        "MAIL_ACCOUNT_1_SMTP_PORT=1025\n"
        "MAIL_ACCOUNT_1_PASSWORD=mockpassword\n"
        "DATA_DIR=data/emails\n"
        "DB_PATH=data/emails/mail_index.db\n"
    ),
    "example.env": (
        "MAIL_ACCOUNT_1_EMAIL=your_email@example.com\n"
        "MAIL_ACCOUNT_1_IMAP_HOST=imap.example.com\n"
        "MAIL_ACCOUNT_1_IMAP_PORT=993\n"
        "MAIL_ACCOUNT_1_SMTP_HOST=smtp.example.com\n"
        "MAIL_ACCOUNT_1_SMTP_PORT=587\n"
        "MAIL_ACCOUNT_1_PASSWORD=your_password\n"
        "DATA_DIR=data/emails\n"
        "DB_PATH=data/emails/mail_index.db\n"
    ),
}

for relpath, content in distractor_files.items():
    fpath = WORKSPACE / relpath
    fpath.write_text(content)

# ── Seed the SQLite database with realistic compliance emails ─────────────────
DB_PATH = WORKSPACE / "data/emails/mail_index.db"

COMPLIANCE_OFFICER = "margaret.thornton@finregulator.gov"
OTHER_SENDERS = [
    "ceo@finfirm.com",
    "hr@finfirm.com",
    "it-support@finfirm.com",
    "noreply@bankingsystem.com",
    "alerts@trading-platform.com",
    "legal@partner-law.com",
    "auditors@kpmg-mock.com",
    "newsletter@fintech-daily.com",
    "support@compliance-tools.io",
    "payroll@finfirm.com",
]

COMPLIANCE_SUBJECTS = [
    "Re: Q1 2024 Regulatory Filing - Urgent Review Required",
    "AML Policy Update - Mandatory Acknowledgment",
    "Suspicious Transaction Report #STR-2024-0042",
    "Annual Compliance Training Deadline - March 31",
    "MiFID II Reporting Discrepancy - Immediate Action",
]

COMPLIANCE_BODIES = [
    "Dear Team,\n\nPlease review the attached Q1 2024 regulatory filing immediately. We have identified three discrepancies in the derivatives reporting section that must be corrected before the March 15 deadline. Failure to comply may result in penalties under Section 7(b) of the Dodd-Frank Act.\n\nAction required: Confirm receipt and assign a case handler by EOD.\n\nRegards,\nMargaret Thornton\nChief Compliance Officer\nFin Regulator",
    "All staff,\n\nEffective immediately, our Anti-Money Laundering policy has been updated per FATF guidance 2024/03. All relationship managers must complete the mandatory re-certification by February 28. Non-compliance will be escalated to the board.\n\nMargaret Thornton",
    "This is a formal notice regarding Suspicious Transaction Report #STR-2024-0042 filed on January 29. The transaction in question involves account ending 7734. Legal hold has been placed. Do not discuss this matter outside the compliance channel.\n\nMargaret Thornton, CCO",
    "Reminder: Annual compliance training must be completed by March 31. HR has noted that 23 employees are currently non-compliant. Please forward this to your teams.\n\nMargaret Thornton",
    "We have identified a MiFID II reporting discrepancy in the January batch. The position data for 14 instruments was submitted incorrectly. Immediate corrective action is required. Please respond with your corrective action plan within 48 hours.\n\nMargaret Thornton",
]

OTHER_SUBJECTS = [
    "Monthly payroll processed",
    "IT maintenance window this Saturday",
    "New coffee machine in the 3rd floor kitchen",
    "Q4 board meeting minutes",
    "Password expiry reminder",
    "Invitation: All-hands meeting Feb 15",
    "Trading platform maintenance",
    "Newsletter: FinTech Trends February 2024",
    "Legal: Updated NDA template",
    "Urgent: VPN client update required",
    "RE: Budget approval for Q1 initiatives",
    "Welcome to the team, Sarah!",
    "Lunch order confirmation",
    "Security alert: unusual login attempt",
    "Audit schedule for March",
]

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    account TEXT NOT NULL,
    folder TEXT NOT NULL,
    subject TEXT,
    sender TEXT,
    recipients TEXT,
    date TEXT,
    body_text TEXT,
    is_read INTEGER DEFAULT 0,
    is_starred INTEGER DEFAULT 0,
    has_attachments INTEGER DEFAULT 0,
    local_path TEXT,
    fetch_task_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fetch_tasks (
    task_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    account TEXT,
    fetched_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT
);
""")

base_date = datetime(2024, 2, 1, 9, 0, 0)

# Insert 5 compliance officer emails
compliance_msg_ids = []
for i, (subj, body) in enumerate(zip(COMPLIANCE_SUBJECTS, COMPLIANCE_BODIES)):
    email_date = base_date + timedelta(days=i * 3, hours=random.randint(0, 8))
    msg_id = f"<compliance-{i+1:04d}-{hashlib.md5(subj.encode()).hexdigest()[:8]}@finregulator.gov>"
    compliance_msg_ids.append(msg_id)
    cur.execute("""
        INSERT OR IGNORE INTO emails
        (message_id, account, folder, subject, sender, recipients, date, body_text, is_read, is_starred, has_attachments, local_path, fetch_task_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        msg_id,
        "compliance_audit@finfirm.com",
        "INBOX",
        subj,
        COMPLIANCE_OFFICER,
        "compliance_audit@finfirm.com",
        email_date.isoformat(),
        body,
        0,
        1,
        1 if i == 0 else 0,
        f"data/emails/raw/{msg_id.strip('<>').replace('/', '_')}.eml",
        None,
    ))

# Insert ~145 other emails (so total pre-existing = 150, plus the fetch will add more)
other_msg_ids = []
for i in range(145):
    sender = random.choice(OTHER_SENDERS)
    subj = random.choice(OTHER_SUBJECTS) + f" ({i+1})"
    email_date = base_date + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    msg_id = f"<other-{i+1:04d}-{hashlib.md5((subj+sender).encode()).hexdigest()[:8]}@finfirm.com>"
    other_msg_ids.append(msg_id)
    body = f"This is an automated or internal email regarding: {subj}.\n\nPlease review at your earliest convenience.\n\nSender: {sender}"
    cur.execute("""
        INSERT OR IGNORE INTO emails
        (message_id, account, folder, subject, sender, recipients, date, body_text, is_read, is_starred, has_attachments, local_path, fetch_task_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        msg_id,
        "compliance_audit@finfirm.com",
        "INBOX",
        subj,
        sender,
        "compliance_audit@finfirm.com",
        email_date.isoformat(),
        body,
        random.randint(0, 1),
        0,
        0,
        f"data/emails/raw/{msg_id.strip('<>').replace('/', '_')}.eml",
        None,
    ))

conn.commit()
conn.close()

# ── Write mock mail_cli.py ────────────────────────────────────────────────────
# This is the bespoke CLI the skill describes; it simulates async fetch,
# fetch-status polling, summarize, search, read, and export.

MAIL_CLI = r'''#!/usr/bin/env python3
"""
Mock implementation of scripts/mail_cli.py for the compliance audit sandbox.
Simulates the full mail-skill workflow with a local SQLite backend.
"""
import argparse
import sys
import os
import json
import sqlite3
import uuid
import time
import csv
import hashlib
import random
from pathlib import Path
from datetime import datetime, timedelta

# ── Resolve workspace root from script location ───────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent

DB_PATH = WORKSPACE / "data/emails/mail_index.db"
TASK_STATE_FILE = WORKSPACE / "data/emails/fetch_tasks_state.json"
AUDIT_LOG = WORKSPACE / "logs/cli_audit.jsonl"

COMPLIANCE_OFFICER = "margaret.thornton@finregulator.gov"

RANDOM = random.Random(99)

def load_task_state():
    if TASK_STATE_FILE.exists():
        return json.loads(TASK_STATE_FILE.read_text())
    return {}

def save_task_state(state):
    TASK_STATE_FILE.write_text(json.dumps(state, indent=2))

def log_call(command, args_dict):
    """Append every CLI invocation to an audit log for evaluation."""
    entry = {"ts": datetime.utcnow().isoformat(), "command": command, "args": args_dict}
    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# ── FETCH ─────────────────────────────────────────────────────────────────────
def cmd_fetch(args):
    limit = args.limit
    confirm = getattr(args, "confirm", False)
    days = getattr(args, "days", 7)

    log_call("fetch", {"limit": limit, "days": days, "confirm": confirm})

    # Enforce the --confirm rule for > 100
    if limit > 100 and not confirm:
        result = {
            "error": "Fetching more than 100 emails requires the --confirm flag. Please re-run with --confirm.",
            "hint": "Re-run: mail_cli.py fetch --limit <N> --days <D> --confirm"
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    task_id = str(uuid.uuid4())

    # Simulate creating "new" emails (beyond what's already in DB) for the task
    new_emails = []
    base_date = datetime(2024, 2, 10, 10, 0, 0)
    senders = [
        "margaret.thornton@finregulator.gov",
        "ceo@finfirm.com",
        "auditors@kpmg-mock.com",
        "noreply@bankingsystem.com",
        "alerts@trading-platform.com",
    ]
    subjects = [
        "FINAL NOTICE: Regulatory Filing Amendment Required",
        "Board Decision on Compliance Budget",
        "External Audit Kickoff - Scheduling",
        "System Alert: Unusual Access Pattern Detected",
        "Trading Halt Notice - Pending Review",
    ]
    bodies = [
        "This is a final notice from the regulatory body. Your Q1 2024 amended filing is overdue by 5 days. Immediate submission is mandatory to avoid a Level 3 penalty. Contact Margaret Thornton directly.\n\nMargaret Thornton, CCO",
        "The board has approved an additional $250,000 budget for compliance infrastructure. Please coordinate with the CFO office to process the transfer. Details attached.\n\nCEO Office",
        "The external audit team from KPMG is available the week of March 4. Please confirm availability for a kickoff call. All documentation should be prepared in advance.\n\nKPMG Audit Team",
        "Our security system detected an unusual access pattern to the compliance document repository at 03:14 UTC. IP address flagged: 192.168.99.44. Review recommended.\n\nAutomated Security Alert",
        "A trading halt has been initiated pending review of positions in the derivatives book. Compliance sign-off required before trading resumes. ETA: 2 hours.\n\nTrading Operations",
    ]

    actual_count = min(limit, len(subjects))
    for i in range(actual_count):
        sender = senders[i % len(senders)]
        subj = subjects[i % len(subjects)]
        body = bodies[i % len(bodies)]
        email_date = base_date + timedelta(days=i, hours=RANDOM.randint(0, 5))
        msg_id = f"<task-{task_id[:8]}-new-{i+1:03d}-{hashlib.md5((subj+sender+task_id).encode()).hexdigest()[:8]}@finregulator.gov>"
        new_emails.append({
            "message_id": msg_id,
            "subject": subj,
            "sender": sender,
            "date": email_date.isoformat(),
            "body_text": body,
            "task_id": task_id,
        })

    state = load_task_state()
    state[task_id] = {
        "status": "running",
        "created_at": datetime.utcnow().isoformat(),
        "limit": limit,
        "days": days,
        "new_emails": new_emails,
        "completed_at": None,
        "fetched_count": 0,
    }
    save_task_state(state)

    result = {
        "task_id": task_id,
        "status": "running",
        "message": f"Fetch task started. Use fetch-status '{task_id}' to check progress."
    }
    print(json.dumps(result, indent=2))

# ── FETCH-STATUS ──────────────────────────────────────────────────────────────
def cmd_fetch_status(args):
    task_id = args.task_id
    log_call("fetch-status", {"task_id": task_id})

    state = load_task_state()
    if task_id not in state:
        print(json.dumps({"error": f"Task {task_id} not found."}))
        sys.exit(1)

    task = state[task_id]

    # Simulate progression: first call → running, second call onwards → completed
    call_count_file = WORKSPACE / f"tmp/fetch_status_calls_{task_id[:8]}.cnt"
    call_count_file.parent.mkdir(exist_ok=True)
    count = int(call_count_file.read_text()) if call_count_file.exists() else 0
    count += 1
    call_count_file.write_text(str(count))

    if count >= 2 and task["status"] == "running":
        # Mark as completed and persist new emails into DB
        conn = get_db()
        cur = conn.cursor()
        for em in task["new_emails"]:
            cur.execute("""
                INSERT OR IGNORE INTO emails
                (message_id, account, folder, subject, sender, recipients, date, body_text,
                 is_read, is_starred, has_attachments, local_path, fetch_task_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                em["message_id"],
                "compliance_audit@finfirm.com",
                "INBOX",
                em["subject"],
                em["sender"],
                "compliance_audit@finfirm.com",
                em["date"],
                em["body_text"],
                0, 0, 0,
                f"data/emails/raw/{em['message_id'].strip('<>').replace('/', '_')}.eml",
                task_id,
            ))
        conn.commit()
        conn.close()

        task["status"] = "completed"
        task["completed_at"] = datetime.utcnow().isoformat()
        task["fetched_count"] = len(task["new_emails"])
        state[task_id] = task
        save_task_state(state)

    result = {
        "task_id": task_id,
        "status": task["status"],
        "fetched_count": task.get("fetched_count", 0),
        "created_at": task["created_at"],
        "completed_at": task.get("completed_at"),
    }
    print(json.dumps(result, indent=2))

# ── SUMMARIZE ────────────────────────────────────────────────────────────────
def cmd_summarize(args):
    task_id = getattr(args, "task_id", None)
    limit = getattr(args, "limit", 20)

    log_call("summarize", {"task_id": task_id, "limit": limit})

    conn = get_db()
    cur = conn.cursor()

    if task_id:
        cur.execute("SELECT * FROM emails WHERE fetch_task_id = ?", (task_id,))
    else:
        cur.execute("SELECT * FROM emails ORDER BY date DESC LIMIT ?", (limit,))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        print(json.dumps({"error": "No emails found for the given criteria."}))
        return

    total = len(rows)
    unread = sum(1 for r in rows if not r["is_read"])
    starred = sum(1 for r in rows if r["is_starred"])
    with_attachments = sum(1 for r in rows if r["has_attachments"])

    compliance_emails = [r for r in rows if r["sender"] == COMPLIANCE_OFFICER]
    action_required = [r for r in rows if any(w in (r["subject"] or "").lower() for w in ["urgent", "required", "action", "mandatory", "final notice", "immediate"])]
    verification = [r for r in rows if any(w in (r["subject"] or "").lower() for w in ["verification", "code", "otp", "confirm your"])]

    report_lines = [
        "# Email Inbox Summary Report",
        f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        f"*Task ID: {task_id or 'N/A'}*",
        "",
        "## Overall Statistics",
        f"- **Total Emails:** {total}",
        f"- **Unread:** {unread}",
        f"- **Starred:** {starred}",
        f"- **With Attachments:** {with_attachments}",
        "",
        "## Action Required",
    ]
    if action_required:
        for r in action_required:
            report_lines.append(f"- **[{r['date'][:10]}]** `{r['sender']}` — {r['subject']}")
    else:
        report_lines.append("- None")

    report_lines += ["", "## Compliance / Regulatory Emails"]
    if compliance_emails:
        for r in compliance_emails:
            report_lines.append(f"- **[{r['date'][:10]}]** {r['subject']} (ID: `{r['message_id']}`)")
    else:
        report_lines.append("- None")

    report_lines += ["", "## Verification Codes"]
    if verification:
        for r in verification:
            report_lines.append(f"- [{r['date'][:10]}] {r['subject']}")
    else:
        report_lines.append("- None")

    report_lines += ["", "## Other Emails"]
    others = [r for r in rows if r not in action_required and r not in compliance_emails and r not in verification]
    if others:
        for r in others[:10]:
            report_lines.append(f"- [{r['date'][:10]}] `{r['sender']}` — {r['subject']}")
        if len(others) > 10:
            report_lines.append(f"- ... and {len(others)-10} more.")
    else:
        report_lines.append("- None")

    report = "\n".join(report_lines)
    print(report)

    # Also save the report to a file so eval can find it
    report_dir = WORKSPACE / "reports"
    report_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    if task_id:
        report_file = report_dir / f"summary_{task_id[:8]}_{ts}.md"
    else:
        report_file = report_dir / f"summary_recent_{ts}.md"
    report_file.write_text(report)
    # Also write a canonical pointer for eval
    pointer = WORKSPACE / "reports" / "latest_summary.json"
    pointer.write_text(json.dumps({"file": str(report_file), "task_id": task_id, "total": total}))

# ── SEARCH ───────────────────────────────────────────────────────────────────
def cmd_search(args):
    query = getattr(args, "query", None)
    sender = getattr(args, "sender", None)
    is_read = getattr(args, "is_read", None)
    limit = getattr(args, "limit", 20)

    log_call("search", {"query": query, "sender": sender, "is_read": is_read, "limit": limit})

    conn = get_db()
    cur = conn.cursor()

    conditions = []
    params = []
    if query:
        conditions.append("(subject LIKE ? OR body_text LIKE ?)")
        params += [f"%{query}%", f"%{query}%"]
    if sender:
        conditions.append("sender LIKE ?")
        params.append(f"%{sender}%")
    if is_read is not None:
        conditions.append("is_read = ?")
        params.append(int(is_read))

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    cur.execute(f"SELECT message_id, subject, sender, date, is_read, is_starred FROM emails {where} ORDER BY date DESC LIMIT ?", params + [limit])
    rows = cur.fetchall()
    conn.close()

    results = [dict(r) for r in rows]
    print(json.dumps({"count": len(results), "results": results}, indent=2))

# ── READ ─────────────────────────────────────────────────────────────────────
def cmd_read(args):
    message_id = args.message_id
    log_call("read", {"message_id": message_id})

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM emails WHERE message_id = ?", (message_id,))
    row = cur.fetchone()
    # Mark as read
    if row:
        cur.execute("UPDATE emails SET is_read = 1 WHERE message_id = ?", (message_id,))
        conn.commit()
    conn.close()

    if not row:
        print(json.dumps({"error": f"Email with message_id '{message_id}' not found."}))
        sys.exit(1)

    result = dict(row)
    print(json.dumps(result, indent=2))

# ── SEND ─────────────────────────────────────────────────────────────────────
def cmd_send(args):
    log_call("send", {"to": args.to, "subject": args.subject})
    print(json.dumps({"status": "sent", "to": args.to, "subject": args.subject, "message": "Email queued for delivery (mock)."}))

# ── MARK ─────────────────────────────────────────────────────────────────────
def cmd_mark(args):
    message_id = args.message_id
    log_call("mark", {"message_id": message_id, "read": getattr(args, "read", None), "starred": getattr(args, "starred", None)})
    conn = get_db()
    cur = conn.cursor()
    if getattr(args, "read", None) is not None:
        cur.execute("UPDATE emails SET is_read = ? WHERE message_id = ?", (args.read, message_id))
    if getattr(args, "starred", None) is not None:
        cur.execute("UPDATE emails SET is_starred = ? WHERE message_id = ?", (args.starred, message_id))
    conn.commit()
    conn.close()
    print(json.dumps({"status": "ok", "message_id": message_id}))

# ── MOVE ─────────────────────────────────────────────────────────────────────
def cmd_move(args):
    log_call("move", {"message_id": args.message_id, "folder": args.folder})
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE emails SET folder = ? WHERE message_id = ?", (args.folder, args.message_id))
    conn.commit()
    conn.close()
    print(json.dumps({"status": "ok", "message_id": args.message_id, "folder": args.folder}))

# ── DELETE ───────────────────────────────────────────────────────────────────
def cmd_delete(args):
    log_call("delete", {"message_id": args.message_id})
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM emails WHERE message_id = ?", (args.message_id,))
    conn.commit()
    conn.close()
    print(json.dumps({"status": "deleted", "message_id": args.message_id}))

# ── EXPORT ───────────────────────────────────────────────────────────────────
def cmd_export(args):
    fmt = args.format
    output = args.output
    log_call("export", {"format": fmt, "output": output})

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT message_id, subject, sender, recipients, date, folder, is_read, is_starred, has_attachments, fetch_task_id FROM emails ORDER BY date DESC")
    rows = cur.fetchall()
    conn.close()

    output_path = Path(output) if Path(output).is_absolute() else WORKSPACE / output

    if fmt == "csv":
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["message_id","subject","sender","recipients","date","folder","is_read","is_starred","has_attachments","fetch_task_id"])
            writer.writeheader()
            for r in rows:
                writer.writerow(dict(r))
        print(json.dumps({"status": "exported", "format": fmt, "output": str(output_path), "count": len(rows)}))
    elif fmt == "json":
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps([dict(r) for r in rows], indent=2))
        print(json.dumps({"status": "exported", "format": fmt, "output": str(output_path), "count": len(rows)}))
    else:
        print(json.dumps({"error": f"Unsupported format: {fmt}"}))
        sys.exit(1)

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(prog="mail_cli.py")
    subparsers = parser.add_subparsers(dest="command")

    # fetch
    p_fetch = subparsers.add_parser("fetch")
    p_fetch.add_argument("--limit", type=int, default=50)
    p_fetch.add_argument("--days", type=int, default=7)
    p_fetch.add_argument("--confirm", action="store_true", default=False)

    # fetch-status
    p_fs = subparsers.add_parser("fetch-status")
    p_fs.add_argument("task_id")

    # summarize
    p_sum = subparsers.add_parser("summarize")
    p_sum.add_argument("--task-id", dest="task_id", default=None)
    p_sum.add_argument("--limit", type=int, default=20)

    # search
    p_search = subparsers.add_parser("search")
    p_search.add_argument("--query", default=None)
    p_search.add_argument("--sender", default=None)
    p_search.add_argument("--is-read", dest="is_read", type=int, default=None)
    p_search.add_argument("--limit", type=int, default=20)

    # read
    p_read = subparsers.add_parser("read")
    p_read.add_argument("message_id")

    # send
    p_send = subparsers.add_parser("send")
    p_send.add_argument("--to", required=True)
    p_send.add_argument("--subject", required=True)
    p_send.add_argument("--body", default="")
    p_send.add_argument("--attach", nargs="*", default=[])

    # mark
    p_mark = subparsers.add_parser("mark")
    p_mark.add_argument("message_id")
    p_mark.add_argument("--read", type=int, default=None)
    p_mark.add_argument("--starred", type=int, default=None)

    # move
    p_move = subparsers.add_parser("move")
    p_move.add_argument("message_id")
    p_move.add_argument("folder")

    # delete
    p_delete = subparsers.add_parser("delete")
    p_delete.add_argument("message_id")

    # export
    p_export = subparsers.add_parser("export")
    p_export.add_argument("--format", default="csv", choices=["csv", "json"])
    p_export.add_argument("--output", required=True)

    args = parser.parse_args()

    dispatch = {
        "fetch": cmd_fetch,
        "fetch-status": cmd_fetch_status,
        "summarize": cmd_summarize,
        "search": cmd_search,
        "read": cmd_read,
        "send": cmd_send,
        "mark": cmd_mark,
        "move": cmd_move,
        "delete": cmd_delete,
        "export": cmd_export,
    }

    if args.command not in dispatch:
        parser.print_help()
        sys.exit(1)

    dispatch[args.command](args)

if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts/mail_cli.py").write_text(MAIL_CLI)

# ── requirements.txt ──────────────────────────────────────────────────────────
(WORKSPACE / "requirements.txt").write_text(
    "python-dotenv\nimap-tools\nbeautifulsoup4\nrequests\n"
)

print("✓ Workspace generated successfully.")
print(f"  DB: {DB_PATH}")
print(f"  mail_cli.py: {WORKSPACE / 'scripts/mail_cli.py'}")