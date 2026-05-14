#!/bin/bash
set -e

# Create the smart-cron CLI tool implementation
cat > /usr/local/bin/smart-cron << 'SMARTCRON_EOF'
#!/usr/bin/env python3
"""
smart-cron - Natural Language Cron Scheduler for OpenClaw
Mock implementation matching SKILL.md specification exactly.
"""
import sys
import os
import json
import sqlite3
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path.home() / ".openclaw" / "workspace" / "smart-cron-data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "jobs.db"
CONFIG_PATH = DATA_DIR / "config.json"

# --- Natural language to cron mapping (exact from SKILL.md) ---
SCHEDULE_MAP = [
    (r"^every\s+5\s+minutes?$",                    "*/5 * * * *"),
    (r"^every\s+hour$",                             "0 * * * *"),
    (r"^every\s+2\s+hours?$",                       "0 */2 * * *"),
    (r"^every\s+30\s+minutes?$",                    "*/30 * * * *"),
    (r"^every\s+(\d+)\s+minutes?$",                 None),   # dynamic
    (r"^every\s+(\d+)\s+hours?$",                   None),   # dynamic
    (r"^every\s+day\s+at\s+9am$",                   "0 9 * * *"),
    (r"^every\s+weekday\s+at\s+9am$",               "0 9 * * 1-5"),
    (r"^every\s+weekday\s+at\s+(\d+)(am|pm)$",      None),   # dynamic
    (r"^every\s+weekend\s+at\s+noon$",              "0 12 * * 6,0"),
    (r"^every\s+weekend\s+at\s+(\d+)(am|pm)$",      None),   # dynamic
    (r"^daily\s+at\s+midnight$",                    "0 0 * * *"),
    (r"^every\s+monday\s+at\s+8am$",               "0 8 * * 1"),
    (r"^every\s+friday\s+at\s+5pm$",               "0 17 * * 5"),
    (r"^every\s+monday\s+at\s+(\d+)(am|pm)$",      None),   # dynamic
    (r"^first\s+monday\s+of\s+month",              "DYNAMIC"),
    (r"^1st\s+of\s+month\s+at\s+9am$",            "0 9 1 * *"),
    (r"^1st\s+of\s+month\s+at\s+(\d+)(am|pm)$",   None),   # dynamic
    (r"^last\s+day\s+of\s+month$",                 "DYNAMIC"),
    (r"^every\s+day\s+at\s+(\d+)(am|pm)$",         None),   # dynamic
]

def parse_time_to_hour(val, ampm):
    h = int(val)
    if ampm == "pm" and h != 12:
        h += 12
    elif ampm == "am" and h == 12:
        h = 0
    return h

def resolve_schedule(expr):
    expr_lower = expr.strip().lower()
    
    # Check if it's already a cron expression (5 fields)
    parts = expr_lower.split()
    if len(parts) == 5 and all(re.match(r'^[\d\*\/,\-]+$', p) for p in parts):
        return expr.strip()
    
    # every N minutes
    m = re.match(r"^every\s+(\d+)\s+minutes?$", expr_lower)
    if m:
        n = int(m.group(1))
        return f"*/{n} * * * *"
    
    # every N hours
    m = re.match(r"^every\s+(\d+)\s+hours?$", expr_lower)
    if m:
        n = int(m.group(1))
        return f"0 */{n} * * *"
    
    # every hour
    if re.match(r"^every\s+hour$", expr_lower):
        return "0 * * * *"
    
    # every 5 minutes
    if re.match(r"^every\s+5\s+minutes?$", expr_lower):
        return "*/5 * * * *"
    
    # every 30 minutes
    if re.match(r"^every\s+30\s+minutes?$", expr_lower):
        return "*/30 * * * *"

    # every weekday at Xam/pm
    m = re.match(r"^every\s+weekday\s+at\s+(\d+)(am|pm)$", expr_lower)
    if m:
        h = parse_time_to_hour(m.group(1), m.group(2))
        return f"0 {h} * * 1-5"
    
    # every weekend at noon
    if re.match(r"^every\s+weekend\s+at\s+noon$", expr_lower):
        return "0 12 * * 6,0"
    
    # every weekend at Xam/pm
    m = re.match(r"^every\s+weekend\s+at\s+(\d+)(am|pm)$", expr_lower)
    if m:
        h = parse_time_to_hour(m.group(1), m.group(2))
        return f"0 {h} * * 6,0"
    
    # every day at Xam/pm
    m = re.match(r"^every\s+day\s+at\s+(\d+)(am|pm)$", expr_lower)
    if m:
        h = parse_time_to_hour(m.group(1), m.group(2))
        return f"0 {h} * * *"
    
    # every day at 9am
    if re.match(r"^every\s+day\s+at\s+9am$", expr_lower):
        return "0 9 * * *"
    
    # every weekday at 9am
    if re.match(r"^every\s+weekday\s+at\s+9am$", expr_lower):
        return "0 9 * * 1-5"
    
    # daily at midnight
    if re.match(r"^daily\s+at\s+midnight$", expr_lower):
        return "0 0 * * *"
    
    # 1st of month at 9am
    if re.match(r"^1st\s+of\s+month\s+at\s+9am$", expr_lower):
        return "0 9 1 * *"
    
    # 1st of month at Xam/pm
    m = re.match(r"^1st\s+of\s+month\s+at\s+(\d+)(am|pm)$", expr_lower)
    if m:
        h = parse_time_to_hour(m.group(1), m.group(2))
        return f"0 {h} 1 * *"

    # every Monday at 8am
    if re.match(r"^every\s+monday\s+at\s+8am$", expr_lower):
        return "0 8 * * 1"
    
    # every Friday at 5pm
    if re.match(r"^every\s+friday\s+at\s+5pm$", expr_lower):
        return "0 17 * * 5"
    
    # first Monday of month
    if re.match(r"^first\s+monday\s+of\s+month", expr_lower):
        return "DYNAMIC:first-monday"
    
    # last day of month
    if re.match(r"^last\s+day\s+of\s+month", expr_lower):
        return "DYNAMIC:last-day"
    
    return None


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            schedule_expr TEXT NOT NULL,
            cron_expr TEXT NOT NULL,
            task TEXT NOT NULL,
            timezone TEXT DEFAULT 'UTC',
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            last_run TEXT,
            next_run TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            run_at TEXT NOT NULL,
            status TEXT NOT NULL,
            output TEXT
        )
    """)
    conn.commit()
    return conn


def cmd_add(args):
    if len(args) < 1:
        print("Usage: smart-cron add <schedule> --task <task> [--timezone TZ]", file=sys.stderr)
        sys.exit(1)
    
    schedule_expr = args[0]
    task = None
    tz = "UTC"
    
    i = 1
    while i < len(args):
        if args[i] == "--task" and i+1 < len(args):
            task = args[i+1]; i += 2
        elif args[i] == "--timezone" and i+1 < len(args):
            tz = args[i+1]; i += 2
        else:
            i += 1
    
    if not task:
        print("Error: --task is required", file=sys.stderr)
        sys.exit(1)
    
    cron_expr = resolve_schedule(schedule_expr)
    if cron_expr is None:
        print(f"Error: Could not parse schedule expression: '{schedule_expr}'", file=sys.stderr)
        sys.exit(1)
    
    job_id = "job-" + str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    
    db = get_db()
    db.execute(
        "INSERT INTO jobs (id, schedule_expr, cron_expr, task, timezone, status, created_at) VALUES (?,?,?,?,?,?,?)",
        (job_id, schedule_expr, cron_expr, task, tz, "active", now)
    )
    db.commit()
    db.close()
    
    print(f"✓ Job scheduled: {job_id}")
    print(f"  Schedule: {schedule_expr}")
    print(f"  Cron:     {cron_expr}")
    print(f"  Task:     {task}")
    print(f"  Timezone: {tz}")


def cmd_list(args):
    db = get_db()
    rows = db.execute("SELECT * FROM jobs ORDER BY created_at").fetchall()
    db.close()
    
    if not rows:
        print("No jobs scheduled.")
        return
    
    print(f"{'ID':<20} {'STATUS':<10} {'SCHEDULE':<35} {'TIMEZONE':<22} {'TASK'}")
    print("-" * 120)
    for r in rows:
        print(f"{r['id']:<20} {r['status']:<10} {r['schedule_expr']:<35} {r['timezone']:<22} {r['task']}")


def cmd_pause(args):
    if not args:
        print("Usage: smart-cron pause <job-id>", file=sys.stderr); sys.exit(1)
    job_id = args[0]
    db = get_db()
    cur = db.execute("UPDATE jobs SET status='paused' WHERE id=?", (job_id,))
    if cur.rowcount == 0:
        print(f"Error: Job '{job_id}' not found.", file=sys.stderr); db.close(); sys.exit(1)
    db.commit(); db.close()
    print(f"✓ Job {job_id} paused.")


def cmd_resume(args):
    if not args:
        print("Usage: smart-cron resume <job-id>", file=sys.stderr); sys.exit(1)
    job_id = args[0]
    db = get_db()
    cur = db.execute("UPDATE jobs SET status='active' WHERE id=?", (job_id,))
    if cur.rowcount == 0:
        print(f"Error: Job '{job_id}' not found.", file=sys.stderr); db.close(); sys.exit(1)
    db.commit(); db.close()
    print(f"✓ Job {job_id} resumed.")


def cmd_remove(args):
    if not args:
        print("Usage: smart-cron remove <job-id>", file=sys.stderr); sys.exit(1)
    job_id = args[0]
    db = get_db()
    cur = db.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    if cur.rowcount == 0:
        print(f"Error: Job '{job_id}' not found.", file=sys.stderr); db.close(); sys.exit(1)
    db.commit(); db.close()
    print(f"✓ Job {job_id} removed.")


def cmd_next(args):
    db = get_db()
    rows = db.execute("SELECT * FROM jobs ORDER BY created_at").fetchall()
    db.close()
    if not rows:
        print("No jobs scheduled."); return
    print(f"{'ID':<20} {'SCHEDULE':<35} {'NEXT RUN (approx)'}")
    print("-" * 80)
    for r in rows:
        print(f"{r['id']:<20} {r['schedule_expr']:<35} (calculated from cron: {r['cron_expr']})")


def cmd_logs(args):
    db = get_db()
    if args:
        rows = db.execute("SELECT * FROM logs WHERE job_id=? ORDER BY run_at DESC LIMIT 20", (args[0],)).fetchall()
    else:
        rows = db.execute("SELECT * FROM logs ORDER BY run_at DESC LIMIT 50").fetchall()
    db.close()
    if not rows:
        print("No logs found."); return
    for r in rows:
        print(f"[{r['run_at']}] {r['job_id']} -> {r['status']}: {r['output']}")


def cmd_run(args):
    if not args:
        print("Usage: smart-cron run <job-id>", file=sys.stderr); sys.exit(1)
    job_id = args[0]
    db = get_db()
    row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        print(f"Error: Job '{job_id}' not found.", file=sys.stderr); db.close(); sys.exit(1)
    now = datetime.now(timezone.utc).isoformat()
    db.execute("INSERT INTO logs (job_id, run_at, status, output) VALUES (?,?,?,?)",
               (job_id, now, "success", f"Ran task: {row['task']}"))
    db.execute("UPDATE jobs SET last_run=? WHERE id=?", (now, job_id))
    db.commit(); db.close()
    print(f"✓ Job {job_id} executed: {row['task']}")


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: smart-cron <command> [options]"); sys.exit(0)
    
    cmd = args[0]
    rest = args[1:]
    
    dispatch = {
        "add": cmd_add,
        "list": cmd_list,
        "pause": cmd_pause,
        "resume": cmd_resume,
        "remove": cmd_remove,
        "next": cmd_next,
        "logs": cmd_logs,
        "run": cmd_run,
    }
    
    if cmd not in dispatch:
        print(f"Unknown command: {cmd}", file=sys.stderr); sys.exit(1)
    
    dispatch[cmd](rest)

if __name__ == "__main__":
    main()
SMARTCRON_EOF

chmod +x /usr/local/bin/smart-cron

echo "smart-cron CLI installed at /usr/local/bin/smart-cron"
smart-cron list