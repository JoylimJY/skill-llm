import os
import random
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

random.seed(42)

workspace = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "skills/neomano-todo/scripts",
    "skills/neomano-todo/docs",
    "fleet/trucks/unit-07",
    "fleet/trucks/unit-12",
    "fleet/maintenance/logs",
    "fleet/maintenance/reports",
    "ops/scheduling",
    "ops/contacts",
    "finance/invoices",
    "finance/fuel",
    ".openclaw/workspace/data",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "fleet/trucks/unit-07/specs.json": json.dumps({"vin": "1HGCM82633A004352", "year": 2018, "model": "Kenworth T680"}),
    "fleet/trucks/unit-12/specs.json": json.dumps({"vin": "3AKJGLD57FSFV8801", "year": 2020, "model": "Freightliner Cascadia"}),
    "fleet/maintenance/logs/unit-07-2024.csv": "date,type,tech\n2024-01-15,oil_change,Martinez\n2024-03-22,tire_rotation,Lopez\n",
    "fleet/maintenance/logs/unit-12-2024.csv": "date,type,tech\n2024-02-10,brake_inspection,Gomez\n2024-04-05,coolant_flush,Torres\n",
    "fleet/maintenance/reports/q1-summary.txt": "Q1 Fleet Summary\nTotal services: 14\nCost: $3,240\n",
    "ops/scheduling/weekly_routes.json": json.dumps({"week": "2025-W28", "routes": ["Quito-Guayaquil", "Cuenca-Loja"]}),
    "ops/contacts/mechanics.json": json.dumps([{"name": "Carlos Martinez", "phone": "+593987001122"}, {"name": "Ana Torres", "phone": "+593987334455"}]),
    "finance/invoices/INV-2025-041.txt": "Invoice #INV-2025-041\nLubricants supplier\nAmount: $890.00\n",
    "finance/fuel/june-2025.csv": "unit,liters,cost\nunit-07,450,720.00\nunit-12,390,624.00\n",
    ".openclaw/workspace/data/.gitkeep": "",
    "ops/scheduling/reminders_draft.txt": "Draft reminders – not yet scheduled\n- Unit 07 DOT inspection: 2025-08-01\n- Unit 12 emission test: 2025-09-15\n",
}
for rel, content in distractors.items():
    (workspace / rel).write_text(content)

# ── the actual todo.py helper script ────────────────────────────────────────
todo_py = r'''#!/usr/bin/env python3
"""
neomano-todo helper script
"""
import argparse, json, os, sqlite3, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

DEFAULT_DB = Path.home() / ".openclaw" / "workspace" / "data" / "neomano-todo.sqlite3"
DB_PATH = Path(os.environ.get("NEOMANO_TODO_DB_PATH", str(DEFAULT_DB)))

VALID_STATUSES = {"open", "done", "blocked", "expired", "forgotten"}

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            notes TEXT,
            priority INTEGER NOT NULL DEFAULT 2,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_touched_at TEXT NOT NULL,
            completed_at TEXT,
            due_at TEXT,
            remind_at TEXT,
            cron_job_id TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_tags (
            task_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (task_id, tag_id),
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    return conn

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_tags(conn, task_id):
    rows = conn.execute(
        "SELECT t.name FROM tags t JOIN task_tags tt ON tt.tag_id=t.id WHERE tt.task_id=?",
        (task_id,)
    ).fetchall()
    return [r["name"] for r in rows]

def task_to_dict(conn, row):
    d = dict(row)
    d["tags"] = get_tags(conn, row["id"])
    return d

def cmd_add(args):
    conn = get_conn()
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO tasks (title,notes,priority,status,created_at,updated_at,last_touched_at,due_at,remind_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (args.title, args.notes, args.priority, "open", ts, ts, ts, args.due_at, args.remind_at)
    )
    task_id = cur.lastrowid
    if args.tags:
        for tag in [t.strip() for t in args.tags.split(",") if t.strip()]:
            conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
            tag_id = conn.execute("SELECT id FROM tags WHERE name=?", (tag,)).fetchone()["id"]
            conn.execute("INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?,?)", (task_id, tag_id))
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    print(json.dumps({"ok": True, "task": task_to_dict(conn, row)}))

def cmd_get(args):
    conn = get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (args.id,)).fetchone()
    if not row:
        print(json.dumps({"ok": False, "error": "not found"})); return
    print(json.dumps({"ok": True, "task": task_to_dict(conn, row)}))

def cmd_list(args):
    conn = get_conn()
    q = "SELECT DISTINCT t.* FROM tasks t"
    params = []
    if args.tag:
        q += " JOIN task_tags tt ON tt.task_id=t.id JOIN tags tg ON tg.id=tt.tag_id"
    q += " WHERE 1=1"
    if args.status:
        q += " AND t.status=?"; params.append(args.status)
    if args.tag:
        q += " AND tg.name=?"; params.append(args.tag)
    order_map = {"priority": "t.priority ASC, t.created_at ASC",
                 "due": "t.due_at ASC NULLS LAST",
                 "created": "t.created_at ASC",
                 "updated": "t.updated_at DESC"}
    q += f" ORDER BY {order_map.get(args.order, 't.created_at ASC')}"
    rows = conn.execute(q, params).fetchall()
    print(json.dumps({"ok": True, "tasks": [task_to_dict(conn, r) for r in rows]}))

def cmd_done(args):
    conn = get_conn()
    ts = now_iso()
    conn.execute("UPDATE tasks SET status='done', completed_at=?, updated_at=?, last_touched_at=? WHERE id=?", (ts, ts, ts, args.id))
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (args.id,)).fetchone()
    print(json.dumps({"ok": True, "task": task_to_dict(conn, row)}))

def cmd_reopen(args):
    conn = get_conn()
    ts = now_iso()
    conn.execute("UPDATE tasks SET status='open', completed_at=NULL, updated_at=?, last_touched_at=? WHERE id=?", (ts, ts, args.id))
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (args.id,)).fetchone()
    print(json.dumps({"ok": True, "task": task_to_dict(conn, row)}))

def cmd_set_status(args):
    if args.status not in VALID_STATUSES:
        print(json.dumps({"ok": False, "error": f"invalid status: {args.status}"})); return
    conn = get_conn()
    ts = now_iso()
    completed_at = ts if args.status == "done" else None
    conn.execute("UPDATE tasks SET status=?, updated_at=?, last_touched_at=?, completed_at=? WHERE id=?",
                 (args.status, ts, ts, completed_at, args.id))
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (args.id,)).fetchone()
    print(json.dumps({"ok": True, "task": task_to_dict(conn, row)}))

def cmd_set_priority(args):
    if args.priority not in (1, 2, 3):
        print(json.dumps({"ok": False, "error": "priority must be 1, 2, or 3"})); return
    conn = get_conn()
    ts = now_iso()
    conn.execute("UPDATE tasks SET priority=?, updated_at=?, last_touched_at=? WHERE id=?",
                 (args.priority, ts, ts, args.id))
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (args.id,)).fetchone()
    print(json.dumps({"ok": True, "task": task_to_dict(conn, row)}))

def cmd_set_tags(args):
    conn = get_conn()
    ts = now_iso()
    conn.execute("DELETE FROM task_tags WHERE task_id=?", (args.id,))
    for tag in [t.strip() for t in args.tags.split(",") if t.strip()]:
        conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
        tag_id = conn.execute("SELECT id FROM tags WHERE name=?", (tag,)).fetchone()["id"]
        conn.execute("INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?,?)", (args.id, tag_id))
    conn.execute("UPDATE tasks SET updated_at=?, last_touched_at=? WHERE id=?", (ts, ts, args.id))
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (args.id,)).fetchone()
    print(json.dumps({"ok": True, "task": task_to_dict(conn, row)}))

def cmd_set_dates(args):
    conn = get_conn()
    ts = now_iso()
    updates = []
    params = []
    if args.due_at is not None:
        updates.append("due_at=?"); params.append(args.due_at)
    if args.remind_at is not None:
        updates.append("remind_at=?"); params.append(args.remind_at)
    updates += ["updated_at=?", "last_touched_at=?"]
    params += [ts, ts, args.id]
    conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id=?", params)
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (args.id,)).fetchone()
    print(json.dumps({"ok": True, "task": task_to_dict(conn, row)}))

def cmd_set_cron_job(args):
    conn = get_conn()
    ts = now_iso()
    conn.execute("UPDATE tasks SET cron_job_id=?, updated_at=?, last_touched_at=? WHERE id=?",
                 (args.cron_job_id, ts, ts, args.id))
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (args.id,)).fetchone()
    print(json.dumps({"ok": True, "task": task_to_dict(conn, row)}))

def cmd_delete(args):
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id=?", (args.id,))
    conn.commit()
    print(json.dumps({"ok": True, "deleted_id": args.id}))

def cmd_stale_candidates(args):
    conn = get_conn()
    now = datetime.now(timezone.utc)
    p3_cutoff = (now - timedelta(days=30)).isoformat()
    p2_cutoff = (now - timedelta(days=45)).isoformat()
    rows = conn.execute("""
        SELECT * FROM tasks
        WHERE status='open' AND (
            (priority=3 AND last_touched_at < ?)
            OR
            (priority=2 AND last_touched_at < ?)
        )
        ORDER BY priority ASC, last_touched_at ASC
    """, (p3_cutoff, p2_cutoff)).fetchall()
    print(json.dumps({"ok": True, "stale_candidates": [task_to_dict(conn, r) for r in rows]}))

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")

    # add
    pa = sub.add_parser("add")
    pa.add_argument("title")
    pa.add_argument("--priority", type=int, default=2)
    pa.add_argument("--tags", default="")
    pa.add_argument("--notes", default=None)
    pa.add_argument("--due-at", dest="due_at", default=None)
    pa.add_argument("--remind-at", dest="remind_at", default=None)

    # get
    pg = sub.add_parser("get"); pg.add_argument("id", type=int)

    # list
    pl = sub.add_parser("list")
    pl.add_argument("--status", default=None)
    pl.add_argument("--tag", default=None)
    pl.add_argument("--order", default="created")

    # done / reopen
    pd = sub.add_parser("done"); pd.add_argument("id", type=int)
    pr = sub.add_parser("reopen"); pr.add_argument("id", type=int)

    # set-status
    pss = sub.add_parser("set-status")
    pss.add_argument("id", type=int)
    pss.add_argument("status")

    # set-priority
    psp = sub.add_parser("set-priority")
    psp.add_argument("id", type=int)
    psp.add_argument("priority", type=int)

    # set-tags
    pst = sub.add_parser("set-tags")
    pst.add_argument("id", type=int)
    pst.add_argument("tags")

    # set-dates
    psd = sub.add_parser("set-dates")
    psd.add_argument("id", type=int)
    psd.add_argument("--due-at", dest="due_at", default=None)
    psd.add_argument("--remind-at", dest="remind_at", default=None)

    # set-cron-job
    pscj = sub.add_parser("set-cron-job")
    pscj.add_argument("id", type=int)
    pscj.add_argument("cron_job_id")

    # delete
    pdl = sub.add_parser("delete"); pdl.add_argument("id", type=int)

    # stale-candidates
    sub.add_parser("stale-candidates")

    args = p.parse_args()
    dispatch = {
        "add": cmd_add, "get": cmd_get, "list": cmd_list,
        "done": cmd_done, "reopen": cmd_reopen,
        "set-status": cmd_set_status, "set-priority": cmd_set_priority,
        "set-tags": cmd_set_tags, "set-dates": cmd_set_dates,
        "set-cron-job": cmd_set_cron_job, "delete": cmd_delete,
        "stale-candidates": cmd_stale_candidates,
    }
    if args.cmd not in dispatch:
        p.print_help(); sys.exit(1)
    dispatch[args.cmd](args)

if __name__ == "__main__":
    main()
'''
(workspace / "skills/neomano-todo/scripts/todo.py").write_text(todo_py)
os.chmod(workspace / "skills/neomano-todo/scripts/todo.py", 0o755)

# ── pre-seed some tasks directly into the DB with manipulated timestamps ──
import subprocess, sys

db_path = workspace / ".openclaw/workspace/data/neomano-todo.sqlite3"
db_path.parent.mkdir(parents=True, exist_ok=True)

env = os.environ.copy()
env["NEOMANO_TODO_DB_PATH"] = str(db_path)

now = datetime.now(timezone.utc)

# Helper to insert a task with a custom last_touched_at
def insert_task(conn, title, notes, priority, status, days_ago, due_at=None, remind_at=None, tags=None):
    ts_now = now.isoformat()
    ts_old = (now - timedelta(days=days_ago)).isoformat()
    cur = conn.execute(
        """INSERT INTO tasks (title,notes,priority,status,created_at,updated_at,last_touched_at,due_at,remind_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (title, notes, priority, status, ts_old, ts_old, ts_old, due_at, remind_at)
    )
    task_id = cur.lastrowid
    if tags:
        for tag in tags:
            conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
            tag_id = conn.execute("SELECT id FROM tags WHERE name=?", (tag,)).fetchone()[0]
            conn.execute("INSERT OR IGNORE INTO task_tags (task_id,tag_id) VALUES (?,?)", (task_id, tag_id))
    return task_id

# Bootstrap the DB schema first via a dummy add+delete
import sqlite3 as _sq
_conn = _sq.connect(str(db_path))
_conn.row_factory = _sq.Row
_conn.execute("PRAGMA journal_mode=WAL")
_conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, notes TEXT,
    priority INTEGER NOT NULL DEFAULT 2, status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_touched_at TEXT NOT NULL,
    completed_at TEXT, due_at TEXT, remind_at TEXT, cron_job_id TEXT)""")
_conn.execute("""CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)""")
_conn.execute("""CREATE TABLE IF NOT EXISTS task_tags (
    task_id INTEGER NOT NULL, tag_id INTEGER NOT NULL,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE)""")
_conn.commit()

# Task A: P3, 35 days old → STALE (should be forgotten)
id_a = insert_task(_conn, "Replace wiper blades on unit-07", "Both front wipers", 3, "open", 35,
                   tags=["maintenance", "unit-07"])

# Task B: P2, 50 days old → STALE (should be forgotten)
id_b = insert_task(_conn, "Update insurance documents for unit-12", "Annual renewal paperwork", 2, "open", 50,
                   tags=["admin", "unit-12"])

# Task C: P3, 20 days old → NOT stale yet (open, keep)
id_c = insert_task(_conn, "Restock first-aid kits in all trucks", "Check expiry dates too", 3, "open", 20,
                   tags=["safety", "fleet"])

# Task D: P1, 90 days old → P1 never auto-forgotten; but should be ESCALATED by agent to include due+remind dates
id_d = insert_task(_conn, "Schedule mandatory DOT annual inspection for unit-07", "Required by law, hefty fine if missed", 1, "open", 90,
                   tags=["compliance", "unit-07"])

# Task E: P2, 10 days old → not stale (open, keep)
id_e = insert_task(_conn, "Coordinate fuel card renewal with finance", "Cards expire end of month", 2, "open", 10,
                   tags=["finance", "admin"])

# Task F: already done (should stay untouched)
id_f = insert_task(_conn, "Install GPS tracker on unit-12", "Completed last sprint", 2, "done", 60,
                   tags=["unit-12", "telematics"])

_conn.commit()
_conn.close()

# Write a manifest so the eval script knows which IDs were created
manifest = {
    "task_a_id": id_a,  # P3 stale → forget
    "task_b_id": id_b,  # P2 stale → forget
    "task_c_id": id_c,  # P3 fresh → keep
    "task_d_id": id_d,  # P1 → escalate priority is already 1; add due+remind dates, set cron job id
    "task_e_id": id_e,  # P2 fresh → keep
    "task_f_id": id_f,  # done → keep as done
    "db_path": str(db_path),
}
(workspace / "ops/.task_manifest.json").write_text(json.dumps(manifest, indent=2))

print("Workspace generation complete.")
print(f"Task IDs: A={id_a}, B={id_b}, C={id_c}, D={id_d}, E={id_e}, F={id_f}")
print(f"DB: {db_path}")