#!/bin/bash
set -e

# ── Clone the actual gtm-system from a local git bundle or reconstruct it ─────
# Since SKILL.md says scripts already exist, we reconstruct the gtm.py CLI
# in a way that is fully functional and matches the documented interface.

GTM_SCRIPTS="/workspace/gtm-system/scripts"
GTM_DATA="/workspace/gtm-system/data"

cat > "$GTM_SCRIPTS/gtm.py" << 'PYEOF'
#!/usr/bin/env python3
"""GTM Tracking System CLI - Expanso/Prometheus"""

import argparse
import sqlite3
import json
import sys
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "gtm.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── contacts ──────────────────────────────────────────────────────────────────
def cmd_add_contact(args):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO contacts (name, email, company, role) VALUES (?, ?, ?, ?)",
        (args.name, args.email, args.company or "", args.role or "")
    )
    conn.commit()
    cid = cur.lastrowid
    print(f"Contact added: id={cid} name='{args.name}' company='{args.company}' role='{args.role}'")
    conn.close()

def cmd_contacts(args):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM contacts ORDER BY id").fetchall()
    if not rows:
        print("No contacts found.")
    for r in rows:
        print(f"[{r['id']}] {r['name']} <{r['email']}> | {r['company']} | {r['role']}")
    conn.close()

# ── opportunities ─────────────────────────────────────────────────────────────
VALID_STAGES = ["awareness", "interest", "evaluation", "negotiation", "closed_won", "closed_lost"]

def cmd_add_opp(args):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO opportunities (company, contact_id, description, stage, priority) VALUES (?, ?, ?, ?, ?)",
        (args.company, args.contact, args.description or "", "awareness", args.priority or 3)
    )
    conn.commit()
    oid = cur.lastrowid
    print(f"Opportunity added: id={oid} company='{args.company}' stage='awareness' priority={args.priority}")
    conn.close()

def cmd_move_stage(args):
    if args.stage not in VALID_STAGES:
        print(f"ERROR: Invalid stage '{args.stage}'. Valid: {VALID_STAGES}", file=sys.stderr)
        sys.exit(1)
    conn = get_conn()
    conn.execute(
        "UPDATE opportunities SET stage=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (args.stage, args.opp_id)
    )
    conn.commit()
    print(f"Opportunity {args.opp_id} moved to stage '{args.stage}'")
    conn.close()

def cmd_log(args):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO interactions (opportunity_id, notes) VALUES (?, ?)",
        (args.opp, args.message)
    )
    conn.commit()
    iid = cur.lastrowid
    print(f"Interaction logged: id={iid} opp_id={args.opp}")
    conn.close()

def cmd_pipeline(args):
    conn = get_conn()
    rows = conn.execute("""
        SELECT o.id, o.company, o.stage, o.priority, c.name as contact_name
        FROM opportunities o
        LEFT JOIN contacts c ON o.contact_id = c.id
        ORDER BY o.priority DESC, o.updated_at DESC
    """).fetchall()
    if not rows:
        print("Pipeline is empty.")
    for r in rows:
        print(f"[{r['id']}] {r['company']} | Stage: {r['stage']} | Priority: {r['priority']} | Contact: {r['contact_name']}")
    conn.close()

# ── reminders ─────────────────────────────────────────────────────────────────
def cmd_remind(args):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (opportunity_id, description, due_date) VALUES (?, ?, ?)",
        (args.opp, args.message, args.date)
    )
    conn.commit()
    rid = cur.lastrowid
    print(f"Reminder set: id={rid} opp_id={args.opp} due='{args.date}'")
    conn.close()

def cmd_complete(args):
    conn = get_conn()
    conn.execute("UPDATE reminders SET completed=1 WHERE id=?", (args.reminder_id,))
    conn.commit()
    print(f"Reminder {args.reminder_id} marked complete.")
    conn.close()

def cmd_actions(args):
    conn = get_conn()
    today = date.today().isoformat()
    rows = conn.execute("""
        SELECT r.id, r.description, r.due_date, o.company
        FROM reminders r
        LEFT JOIN opportunities o ON r.opportunity_id = o.id
        WHERE r.completed=0 AND r.due_date <= ?
        ORDER BY r.due_date ASC
    """, (today,)).fetchall()
    if not rows:
        print("No pending actions.")
    for r in rows:
        print(f"[{r['id']}] [{r['due_date']}] {r['description']} | Opp: {r['company']}")
    conn.close()

# ── keywords ──────────────────────────────────────────────────────────────────
VALID_CATEGORIES = ["domain", "competitor", "use_case", "general"]

def cmd_add_keyword(args):
    if args.category and args.category not in VALID_CATEGORIES:
        print(f"WARNING: Unusual category '{args.category}'. Proceeding.")
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO keywords (keyword, category, weight) VALUES (?, ?, ?)",
            (args.keyword, args.category or "general", args.weight if args.weight is not None else 1.0)
        )
        conn.commit()
        print(f"Keyword added: '{args.keyword}' category='{args.category}' weight={args.weight}")
    except sqlite3.IntegrityError:
        print(f"Keyword '{args.keyword}' already exists.")
    conn.close()

# ── crawl & signals ───────────────────────────────────────────────────────────
def cmd_crawl(args):
    sources = args.sources.split(",") if args.sources else ["hn", "reddit", "github"]
    conn = get_conn()
    inserted = 0
    if "hn" in sources:
        conn.execute(
            "INSERT INTO signals (source, title, url, content, score) VALUES (?, ?, ?, ?, ?)",
            ("hn", "HN: Who is hiring distributed compute engineers?",
             "https://news.ycombinator.com/item?id=88881", "Bacalhau mentioned in thread", 22.0)
        )
        inserted += 1
    if "github" in sources:
        conn.execute(
            "INSERT INTO signals (source, title, url, content, score) VALUES (?, ?, ?, ?, ?)",
            ("github", "New repo using expanso/bacalhau as dependency",
             "https://github.com/someuser/ml-pipeline", "Expanso bacalhau integration", 18.0)
        )
        inserted += 1
    if "reddit" in sources:
        conn.execute(
            "INSERT INTO signals (source, title, url, content, score) VALUES (?, ?, ?, ?, ?)",
            ("reddit", "r/dataengineering: Replacing Airflow with Bacalhau",
             "https://reddit.com/r/dataengineering/comments/abc", "WFH engineer evaluating Bacalhau", 35.0)
        )
        inserted += 1
    conn.commit()
    print(f"Crawl complete. {inserted} new signals from sources: {sources}")
    conn.close()

def cmd_signals(args):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM signals WHERE processed=0 ORDER BY score DESC"
    ).fetchall()
    if not rows:
        print("No unprocessed signals.")
    for r in rows:
        print(f"[{r['id']}] [{r['source']}] score={r['score']} | {r['title']}")
    conn.close()

def cmd_process_signal(args):
    conn = get_conn()
    conn.execute("UPDATE signals SET processed=1 WHERE id=?", (args.signal_id,))
    conn.commit()
    print(f"Signal {args.signal_id} marked as processed.")
    conn.close()

def cmd_digest(args):
    conn = get_conn()
    opps = conn.execute("SELECT company, stage FROM opportunities ORDER BY updated_at DESC LIMIT 5").fetchall()
    signals = conn.execute("SELECT COUNT(*) as cnt FROM signals WHERE processed=0").fetchone()
    reminders = conn.execute("SELECT COUNT(*) as cnt FROM reminders WHERE completed=0").fetchone()
    print("=== GTM Daily Digest ===")
    print(f"Unprocessed signals: {signals['cnt']}")
    print(f"Pending reminders: {reminders['cnt']}")
    print("Top opportunities:")
    for o in opps:
        print(f"  - {o['company']}: {o['stage']}")
    conn.close()

# ── parser ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="GTM Tracking CLI")
    sub = parser.add_subparsers(dest="command")

    # contacts
    p = sub.add_parser("add-contact")
    p.add_argument("name"); p.add_argument("email")
    p.add_argument("--company"); p.add_argument("--role")

    sub.add_parser("contacts")

    # opportunities
    p = sub.add_parser("add-opp")
    p.add_argument("company"); p.add_argument("--contact", type=int)
    p.add_argument("--description"); p.add_argument("--priority", type=int, default=3)

    p = sub.add_parser("move-stage")
    p.add_argument("opp_id", type=int); p.add_argument("stage")

    p = sub.add_parser("log")
    p.add_argument("message"); p.add_argument("--opp", type=int)

    sub.add_parser("pipeline")

    # reminders
    p = sub.add_parser("remind")
    p.add_argument("message"); p.add_argument("--opp", type=int); p.add_argument("--date")

    p = sub.add_parser("complete")
    p.add_argument("reminder_id", type=int)

    sub.add_parser("actions")

    # keywords
    p = sub.add_parser("add-keyword")
    p.add_argument("keyword"); p.add_argument("--category", default="general")
    p.add_argument("--weight", type=float, default=1.0)

    # crawl & signals
    p = sub.add_parser("crawl")
    p.add_argument("--sources", default=None)

    sub.add_parser("signals")

    p = sub.add_parser("process-signal")
    p.add_argument("signal_id", type=int)

    sub.add_parser("digest")

    args = parser.parse_args()
    dispatch = {
        "add-contact": cmd_add_contact, "contacts": cmd_contacts,
        "add-opp": cmd_add_opp, "move-stage": cmd_move_stage,
        "log": cmd_log, "pipeline": cmd_pipeline,
        "remind": cmd_remind, "complete": cmd_complete, "actions": cmd_actions,
        "add-keyword": cmd_add_keyword,
        "crawl": cmd_crawl, "signals": cmd_signals,
        "process-signal": cmd_process_signal, "digest": cmd_digest,
    }
    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
PYEOF

chmod +x "$GTM_SCRIPTS/gtm.py"
echo "GTM CLI installed at $GTM_SCRIPTS/gtm.py"

# Write the agent's task instructions (business language only, no CLI hints)
cat > /workspace/task_instructions.md << 'EOF'
# Sales Operations Task Brief

Our team has a new high-priority enterprise prospect to track. Please complete
all of the following using the GTM system (CLI available at
/workspace/gtm-system/scripts/gtm.py):

## Task 1 — New Contact
Add a new contact for our prospect:
- Name: **Jordan Mehta**
- Email: jordan.mehta@vertexsystems.io
- Company: **Vertex Systems**
- Role: **Head of Infrastructure**

## Task 2 — New Opportunity
Create a new pipeline opportunity for Vertex Systems, linked to Jordan Mehta.
Use the description: "Evaluating distributed batch compute for ML pipelines"
Set the priority to **5** (highest).

## Task 3 — Pipeline Advancement
Vertex Systems had a strong discovery call. They are now actively running
trials with our product. Move their opportunity to the appropriate stage
that reflects this (they are beyond initial interest — they are now
**actively evaluating**).

## Task 4 — Log the Interaction
Log the following note against the Vertex Systems opportunity:
"Discovery call completed — team running Bacalhau trial on 3-node cluster, very positive feedback"

## Task 5 — Set a Follow-up Reminder
Set a reminder for the Vertex Systems opportunity to:
"Send custom pricing proposal and ROI analysis"
Due date: **2024-03-01**

## Task 6 — Add Intelligence Keyword
We want to track a new competitive signal. Add the keyword
**"wasm-compute"** to our tracking system.
Category: **domain**
Weight: **2.5**

## Task 7 — Run Intelligence Crawl & Process Signals
Run the full crawl across all available sources to pick up new market
signals. Then mark ALL currently unprocessed signals as processed.

EOF

echo "Task instructions written."
echo "Setup complete."