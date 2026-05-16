import os
import json
import stat
import random
from pathlib import Path

random.seed(42)

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "scripts/utils",
    "references",
    "logs",
    "config_backups",
    "data/raw",
    "data/processed",
    "reports/2024",
    "reports/2025",
    "archive/old_scripts",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "references/providers.md": """\
# Email Provider POP3 Settings

| Provider | Server         | Port | Notes                        |
|----------|---------------|------|------------------------------|
| 163      | pop.163.com   | 995  | Use auth code, not password  |
| QQ       | pop.qq.com    | 995  | Use auth code                |
| Gmail    | pop.gmail.com | 995  | Enable POP in settings       |
| Outlook  | outlook.office365.com | 995 | Use app password       |
""",
    "references/README.md": "Provider reference docs. See providers.md for server configs.\n",
    "logs/app.log": "2025-06-01 INFO: Service started\n2025-06-02 WARN: Timeout on connection\n",
    "logs/error.log": "2025-05-30 ERROR: Auth failed for unknown user\n",
    "config_backups/email_backup.ini": """\
[email]
user   = old_user@163.com
pass_  = OLD_INVALID_CODE
server = pop.163.com
port   = 995
""",
    "config_backups/README.txt": "Old configs - do not use.\n",
    "data/raw/sample_emails.txt": "Subject: Test\nFrom: a@b.com\nDate: 2025-01-01\n\nHello World\n",
    "data/processed/summary.csv": "index,subject,from\n1,Hello,a@b.com\n2,Invoice #1234,billing@vendor.com\n",
    "reports/2024/annual_report.json": json.dumps({"year": 2024, "emails_processed": 1200}),
    "reports/2025/q1_report.json": json.dumps({"year": 2025, "q": 1, "emails_processed": 340}),
    "archive/old_scripts/fetch_mail.py": """\
# Deprecated: use scripts/email_reader.py instead
import smtplib
print('This script is deprecated')
""",
    "scripts/utils/parser.py": """\
# Utility: parse raw email bytes
def parse_subject(raw):
    for line in raw.split('\\n'):
        if line.lower().startswith('subject:'):
            return line[8:].strip()
    return ''
""",
    ".gitignore": "*.pyc\n__pycache__/\nscripts/.email_config\n.env\n",
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

# ── The REAL mock email_reader.py script (pre-existing as per SKILL.md) ─────
# This simulates a working POP3 reader without real network access.
# It reads config from .email_config / env vars / CLI args and returns
# deterministic JSON output.

mock_script = r'''#!/usr/bin/env python3
"""
Mock implementation of scripts/email_reader.py
Behaves identically to the real POP3 reader but uses local fixture data.
Configuration is validated exactly as the real script does.
"""
import argparse
import json
import os
import sys
import configparser
from pathlib import Path

# ── Fixed fixture email data ─────────────────────────────────────────────────
FIXTURE_EMAILS = [
    {"index": 1,  "subject": "Welcome to CloudDesk",         "from": "onboarding@clouddesk.io",   "date": "2025-01-10 09:00:00", "body": "Welcome! Your account is ready."},
    {"index": 2,  "subject": "Your weekly digest",           "from": "digest@newsletter.com",      "date": "2025-01-17 08:00:00", "body": "Here is your weekly summary of news."},
    {"index": 3,  "subject": "Invoice #1001 from VendorCo",  "from": "billing@vendorco.com",       "date": "2025-02-03 14:22:00", "body": "Please find attached Invoice #1001 for $2,500. Due: 2025-03-01. Thank you for your business."},
    {"index": 4,  "subject": "Server maintenance notice",    "from": "ops@infra.internal",         "date": "2025-02-15 07:00:00", "body": "Scheduled maintenance on Feb 20. Expect 2h downtime."},
    {"index": 5,  "subject": "Password reset request",       "from": "noreply@clouddesk.io",       "date": "2025-03-01 11:45:00", "body": "A password reset was requested for your account."},
    {"index": 6,  "subject": "Invoice #1002 overdue",        "from": "billing@vendorco.com",       "date": "2025-03-12 09:30:00", "body": "Invoice #1002 for $1,800 is now overdue. Please pay immediately."},
    {"index": 7,  "subject": "Team meeting agenda",          "from": "manager@company.com",        "date": "2025-03-18 16:00:00", "body": "Agenda for Thursday: 1) Q2 planning 2) Budget review 3) AOB"},
    {"index": 8,  "subject": "Subscription renewal",        "from": "billing@saasapp.com",        "date": "2025-04-01 10:00:00", "body": "Your subscription renews on May 1. Total: $599/year."},
    {"index": 9,  "subject": "Security alert: new login",    "from": "security@clouddesk.io",      "date": "2025-04-22 03:17:00", "body": "A new login was detected from IP 203.0.113.42 (Shanghai, CN)."},
    {"index": 10, "subject": "Invoice #1003 payment received","from": "billing@vendorco.com",      "date": "2025-05-05 12:00:00", "body": "We have received your payment for Invoice #1003. Thank you!"},
    {"index": 11, "subject": "Upcoming feature release",     "from": "product@clouddesk.io",       "date": "2025-05-10 09:00:00", "body": "We are releasing version 3.0 next week. See changelog attached."},
    {"index": 12, "subject": "Support ticket #5521 resolved","from": "support@clouddesk.io",       "date": "2025-05-18 14:30:00", "body": "Your support ticket #5521 has been resolved. Please rate your experience."},
]

VALID_USER   = "support@company163.com"
VALID_PASS   = "AUTHCODE_XK9mP2"
VALID_SERVER = "pop.163.com"
VALID_PORT   = 995


def load_config(args):
    """Three-layer priority: CLI > ENV > .email_config file"""
    cfg = {"user": None, "pass_": None, "server": None, "port": None}

    # Layer 3: .email_config file (lowest priority)
    config_path = Path(__file__).parent / ".email_config"
    if config_path.exists():
        parser = configparser.ConfigParser()
        parser.read(config_path)
        if "email" in parser:
            sec = parser["email"]
            cfg["user"]   = sec.get("user",   cfg["user"])
            cfg["pass_"]  = sec.get("pass_",  cfg["pass_"])
            cfg["server"] = sec.get("server", cfg["server"])
            cfg["port"]   = sec.getint("port", cfg["port"]) if sec.get("port") else cfg["port"]

    # Layer 2: environment variables
    if os.environ.get("EMAIL_USER"):   cfg["user"]   = os.environ["EMAIL_USER"]
    if os.environ.get("EMAIL_PASS"):   cfg["pass_"]  = os.environ["EMAIL_PASS"]
    if os.environ.get("POP3_SERVER"):  cfg["server"] = os.environ["POP3_SERVER"]
    if os.environ.get("POP3_PORT"):    cfg["port"]   = int(os.environ["POP3_PORT"])

    # Layer 1: CLI args (highest priority)
    if getattr(args, "user",   None): cfg["user"]   = args.user
    if getattr(args, "pass_",  None): cfg["pass_"]  = args.pass_
    if getattr(args, "server", None): cfg["server"] = args.server
    if getattr(args, "port",   None): cfg["port"]   = args.port

    return cfg


def validate_config(cfg):
    if cfg["user"] != VALID_USER or cfg["pass_"] != VALID_PASS:
        print(json.dumps({"error": "AUTH_FAILED", "message": "Invalid credentials"}))
        sys.exit(1)
    if cfg["server"] != VALID_SERVER:
        print(json.dumps({"error": "SERVER_ERROR", "message": f"Cannot connect to {cfg['server']}"}))
        sys.exit(1)
    expected_port = VALID_PORT
    if cfg["port"] and int(cfg["port"]) != expected_port:
        print(json.dumps({"error": "PORT_ERROR", "message": f"Port {cfg['port']} rejected"}))
        sys.exit(1)


def cmd_count(cfg, args):
    validate_config(cfg)
    print(json.dumps({"total": len(FIXTURE_EMAILS)}))


def cmd_subjects(cfg, args):
    validate_config(cfg)
    n = min(args.n, len(FIXTURE_EMAILS))
    recent = FIXTURE_EMAILS[-n:][::-1]
    result = []
    for e in recent:
        result.append({"index": e["index"], "subject": e["subject"],
                        "from": e["from"], "date": e["date"]})
    print(json.dumps({"total": len(FIXTURE_EMAILS), "emails": result}))


def cmd_list(cfg, args):
    validate_config(cfg)
    n = min(args.n, len(FIXTURE_EMAILS))
    recent = FIXTURE_EMAILS[-n:][::-1]
    result = []
    for e in recent:
        result.append({"index": e["index"], "subject": e["subject"],
                        "from": e["from"], "date": e["date"], "body": e["body"]})
    print(json.dumps({"total": len(FIXTURE_EMAILS), "emails": result}))


def cmd_read(cfg, args):
    validate_config(cfg)
    idx = args.index
    found = next((e for e in FIXTURE_EMAILS if e["index"] == idx), None)
    if not found:
        print(json.dumps({"error": "NOT_FOUND", "message": f"Email index {idx} not found"}))
        sys.exit(1)
    print(json.dumps({"email": found}))


def cmd_search(cfg, args):
    validate_config(cfg)
    keyword = args.keyword.lower()
    rng = min(args.range, len(FIXTURE_EMAILS))
    pool = FIXTURE_EMAILS[-rng:]
    matches = [e for e in pool if keyword in e["subject"].lower()]
    result = [{"index": e["index"], "subject": e["subject"],
               "from": e["from"], "date": e["date"]} for e in matches]
    print(json.dumps({"total_searched": rng, "matches": len(result), "emails": result}))


def main():
    parser = argparse.ArgumentParser(description="Email Reader (Mock)")
    # Global config flags
    parser.add_argument("--user",   default=None)
    parser.add_argument("--pass_",  default=None)
    parser.add_argument("--server", default=None)
    parser.add_argument("--port",   type=int, default=None)

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("count")

    p_sub = sub.add_parser("subjects")
    p_sub.add_argument("--n", type=int, default=10)

    p_list = sub.add_parser("list")
    p_list.add_argument("--n", type=int, default=5)

    p_read = sub.add_parser("read")
    p_read.add_argument("--index", type=int, required=True)

    p_search = sub.add_parser("search")
    p_search.add_argument("--keyword", required=True)
    p_search.add_argument("--range", type=int, default=100)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cfg = load_config(args)
    dispatch = {
        "count":    cmd_count,
        "subjects": cmd_subjects,
        "list":     cmd_list,
        "read":     cmd_read,
        "search":   cmd_search,
    }
    dispatch[args.command](cfg, args)


if __name__ == "__main__":
    main()
'''

with open("scripts/email_reader.py", "w") as f:
    f.write(mock_script)

# ── Task briefing document (business context only, no technical hints) ───────
briefing = """\
# Customer Support Inbox Audit – Task Brief

The support team mailbox (support@company163.com) has been accumulating emails
and the team lead needs a snapshot audit done TODAY.

Auth code: AUTHCODE_XK9mP2
Mail server type: 163

## Deliverable

Produce a file called `inbox_report.json` in the workspace root with the
following sections (exact key names TBD by the tooling you choose):

1. total_emails   — how many emails are in the mailbox total
2. recent_subjects — subject lines of the 5 most recent emails (header scan only)
3. invoice_emails  — full content of every email whose subject contains "Invoice",
                     searched across the last 50 emails
4. oldest_invoice_full — complete email object for the single oldest invoice email
                         found in step 3 (i.e., the one with the lowest index)

The operations must be performed using the available email tooling in this workspace.
"""

with open("TASK_BRIEF.md", "w") as f:
    f.write(briefing)

# ── A misleading stale config file in the WRONG location ────────────────────
with open(".email_config", "w") as f:
    f.write("""\
[email]
user   = wrong_user@163.com
pass_  = WRONG_CODE
server = pop.163.com
port   = 995
""")

print("Workspace generated successfully.")
print("Files created:", sum(1 for _ in Path(".").rglob("*") if _.is_file()))