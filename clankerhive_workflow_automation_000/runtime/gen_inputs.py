#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the ICU coordination task.
"""
import os
import random
import json
import time
import sqlite3
import stat

random.seed(42)

WORKSPACE = "/workspace"

# ── Helper ────────────────────────────────────────────────────────────────────
def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

def write_bin(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)

# ── 1. Create the clankerhive script ─────────────────────────────────────────
# This is the SKILL script that must exist at scripts/clankerhive.py
clankerhive_script = r'''#!/usr/bin/env python3
"""ClankerHive — Shared SQLite-backed context store for multi-session agent coordination."""
import argparse, json, os, sqlite3, sys, time
from typing import Optional

DB_PATH = os.environ.get("CLANKERHIVE_DB", os.path.expanduser("~/.openclaw/hive.db"))

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS facts (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        expires_at REAL,
        source TEXT,
        created_at REAL NOT NULL DEFAULT (unixepoch())
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        message TEXT NOT NULL,
        claimed INTEGER NOT NULL DEFAULT 0,
        claimed_at REAL,
        created_at REAL NOT NULL DEFAULT (unixepoch())
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
        name TEXT PRIMARY KEY,
        owner TEXT,
        status TEXT NOT NULL DEFAULT 'claimed',
        result TEXT,
        claimed_at REAL NOT NULL DEFAULT (unixepoch()),
        released_at REAL
    )""")
    conn.commit()
    return conn

def prune_expired(conn):
    now = time.time()
    conn.execute("DELETE FROM facts WHERE expires_at IS NOT NULL AND expires_at < ?", (now,))
    conn.commit()

def cmd_set(args):
    conn = get_conn()
    prune_expired(conn)
    expires_at = time.time() + args.ttl if args.ttl else None
    conn.execute(
        "INSERT OR REPLACE INTO facts (key, value, expires_at, source, created_at) VALUES (?,?,?,?,?)",
        (args.key, args.value, expires_at, args.source, time.time())
    )
    conn.commit()
    print("ok")

def cmd_get(args):
    conn = get_conn()
    prune_expired(conn)
    row = conn.execute("SELECT value FROM facts WHERE key=?", (args.key,)).fetchone()
    if row:
        print(row[0])

def cmd_list(args):
    conn = get_conn()
    prune_expired(conn)
    if args.prefix:
        rows = conn.execute("SELECT key, value, expires_at, source FROM facts WHERE key LIKE ?",
                            (args.prefix + "%",)).fetchall()
    else:
        rows = conn.execute("SELECT key, value, expires_at, source FROM facts").fetchall()
    result = [{"key": r[0], "value": r[1], "expires_at": r[2], "source": r[3]} for r in rows]
    print(json.dumps(result))

def cmd_delete(args):
    conn = get_conn()
    conn.execute("DELETE FROM facts WHERE key=?", (args.key,))
    conn.commit()
    print("ok")

def cmd_queue_alert(args):
    conn = get_conn()
    conn.execute("INSERT INTO alerts (topic, message, created_at) VALUES (?,?,?)",
                 (args.topic, args.message, time.time()))
    conn.commit()
    print("ok")

def cmd_list_alerts(args):
    conn = get_conn()
    rows = conn.execute("SELECT id, topic, message, claimed, created_at FROM alerts WHERE claimed=0").fetchall()
    result = [{"id": r[0], "topic": r[1], "message": r[2], "claimed": r[3], "created_at": r[4]} for r in rows]
    print(json.dumps(result))

def cmd_pop_alerts(args):
    conn = get_conn()
    now = time.time()
    if args.topic:
        rows = conn.execute("SELECT id, topic, message FROM alerts WHERE claimed=0 AND topic=?",
                            (args.topic,)).fetchall()
    else:
        rows = conn.execute("SELECT id, topic, message FROM alerts WHERE claimed=0").fetchall()
    ids = [r[0] for r in rows]
    if ids:
        placeholders = ",".join("?" * len(ids))
        conn.execute(f"UPDATE alerts SET claimed=1, claimed_at=? WHERE id IN ({placeholders})",
                     [now] + ids)
        conn.commit()
    result = [{"id": r[0], "topic": r[1], "message": r[2]} for r in rows]
    print(json.dumps(result))

def cmd_purge_alerts(args):
    conn = get_conn()
    cutoff = time.time() - args.age
    cur = conn.execute("DELETE FROM alerts WHERE claimed=1 AND claimed_at < ?", (cutoff,))
    conn.commit()
    print(f"purged {cur.rowcount}")

def cmd_claim_task(args):
    conn = get_conn()
    existing = conn.execute("SELECT owner, status FROM tasks WHERE name=?", (args.name,)).fetchone()
    if existing:
        owner, status = existing
        print(f"already-claimed by {owner}")
        sys.exit(1)
    owner = args.owner or os.environ.get("CLANKERHIVE_OWNER", "agent")
    conn.execute("INSERT INTO tasks (name, owner, status, claimed_at) VALUES (?,?,?,?)",
                 (args.name, owner, "claimed", time.time()))
    conn.commit()
    print("ok")

def cmd_release_task(args):
    conn = get_conn()
    existing = conn.execute("SELECT owner FROM tasks WHERE name=?", (args.name,)).fetchone()
    if not existing:
        print("not-found")
        sys.exit(1)
    conn.execute("UPDATE tasks SET status='done', result=?, released_at=? WHERE name=?",
                 (args.result, time.time(), args.name))
    conn.commit()
    print("ok")

def cmd_task_status(args):
    conn = get_conn()
    row = conn.execute("SELECT name, owner, status, result, claimed_at, released_at FROM tasks WHERE name=?",
                       (args.name,)).fetchone()
    if not row:
        print("not-found")
        sys.exit(1)
    print(json.dumps({"name": row[0], "owner": row[1], "status": row[2],
                       "result": row[3], "claimed_at": row[4], "released_at": row[5]}))

def cmd_stats(args):
    conn = get_conn()
    prune_expired(conn)
    facts_count = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    alerts_pending = conn.execute("SELECT COUNT(*) FROM alerts WHERE claimed=0").fetchone()[0]
    alerts_claimed = conn.execute("SELECT COUNT(*) FROM alerts WHERE claimed=1").fetchone()[0]
    tasks_claimed = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='claimed'").fetchone()[0]
    tasks_done = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0]
    print(json.dumps({
        "facts": facts_count,
        "alerts_pending": alerts_pending,
        "alerts_claimed": alerts_claimed,
        "tasks_claimed": tasks_claimed,
        "tasks_done": tasks_done
    }))

def main():
    parser = argparse.ArgumentParser(description="ClankerHive coordination store")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("set"); p.add_argument("key"); p.add_argument("value")
    p.add_argument("--ttl", type=float, default=None); p.add_argument("--source", default=None)

    p = sub.add_parser("get"); p.add_argument("key")
    p = sub.add_parser("list"); p.add_argument("--prefix", default=None)
    p = sub.add_parser("delete"); p.add_argument("key")

    p = sub.add_parser("queue-alert"); p.add_argument("topic"); p.add_argument("message")
    p = sub.add_parser("list-alerts")
    p = sub.add_parser("pop-alerts"); p.add_argument("--topic", default=None)
    p = sub.add_parser("purge-alerts"); p.add_argument("--age", type=float, default=86400.0)

    p = sub.add_parser("claim-task"); p.add_argument("name"); p.add_argument("--owner", default=None)
    p = sub.add_parser("release-task"); p.add_argument("name"); p.add_argument("--result", default=None)
    p = sub.add_parser("task-status"); p.add_argument("name")
    p = sub.add_parser("stats")

    args = parser.parse_args()
    dispatch = {
        "set": cmd_set, "get": cmd_get, "list": cmd_list, "delete": cmd_delete,
        "queue-alert": cmd_queue_alert, "list-alerts": cmd_list_alerts,
        "pop-alerts": cmd_pop_alerts, "purge-alerts": cmd_purge_alerts,
        "claim-task": cmd_claim_task, "release-task": cmd_release_task,
        "task-status": cmd_task_status, "stats": cmd_stats,
    }
    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

write(f"{WORKSPACE}/scripts/clankerhive.py", clankerhive_script)
os.chmod(f"{WORKSPACE}/scripts/clankerhive.py", 0o755)

# ── 2. Pre-populate the DB with stale "day-shift" state ───────────────────────
# This simulates a messy prior state: some old facts (some expired), old alerts (claimed),
# an already-released task, and one lingering stale claimed task from 30h ago.
db_path = f"{WORKSPACE}/icu_hive.db"
os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else WORKSPACE, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("""CREATE TABLE IF NOT EXISTS facts (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    expires_at REAL,
    source TEXT,
    created_at REAL NOT NULL DEFAULT (unixepoch())
)""")
conn.execute("""CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    message TEXT NOT NULL,
    claimed INTEGER NOT NULL DEFAULT 0,
    claimed_at REAL,
    created_at REAL NOT NULL DEFAULT (unixepoch())
)""")
conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
    name TEXT PRIMARY KEY,
    owner TEXT,
    status TEXT NOT NULL DEFAULT 'claimed',
    result TEXT,
    claimed_at REAL NOT NULL DEFAULT (unixepoch()),
    released_at REAL
)""")

now = time.time()

# Old facts — some expired, some not
conn.execute("INSERT INTO facts VALUES (?,?,?,?,?)",
             ("icu.ventilator_check", str(int(now - 7200)), now - 7200 + 1800, "day-shift", now - 7200))
conn.execute("INSERT INTO facts VALUES (?,?,?,?,?)",
             ("icu.morning_vitals", str(int(now - 10800)), None, "day-shift", now - 10800))
conn.execute("INSERT INTO facts VALUES (?,?,?,?,?)",
             ("icu.x_ray_round", str(int(now - 3600)), now - 3600 + 900, "day-shift", now - 3600))

# Old claimed alerts (from over 30 hours ago — should be purgeable)
old_ts = now - (31 * 3600)
conn.execute("INSERT INTO alerts (topic, message, claimed, claimed_at, created_at) VALUES (?,?,?,?,?)",
             ("equipment", "Ventilator VT-7 battery low — day shift handled", 1, old_ts + 60, old_ts))
conn.execute("INSERT INTO alerts (topic, message, claimed, claimed_at, created_at) VALUES (?,?,?,?,?)",
             ("medication", "Morphine restock completed — day shift handled", 1, old_ts + 120, old_ts))

# One unclaimed leftover alert from day shift (agent should NOT consume this — it's for a different session)
conn.execute("INSERT INTO alerts (topic, message, claimed, claimed_at, created_at) VALUES (?,?,?,?,?)",
             ("equipment", "IV pump calibration overdue — unresolved handoff", 0, None, now - 5400))

# A previously completed task
conn.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?)",
             ("morning-vitals-round", "day-shift-agent", "done", "all vitals recorded", now - 10800, now - 9000))

# A stale "claimed" task from 30h ago (simulating a crashed agent — agent should NOT interact with this)
conn.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?)",
             ("equipment-audit-stale", "crashed-agent-01", "claimed", None, now - 108000, None))

conn.commit()
conn.close()

# ── 3. The shift handoff instructions ─────────────────────────────────────────
handoff_log = """\
ICU OVERNIGHT SHIFT HANDOFF LOG — Night Shift Coordination Setup
================================================================
Prepared by: Dr. Elara Voss, Charge Nurse (Day Shift Lead)
Time: End of Day Shift

COORDINATION SYSTEM SETUP REQUIRED FOR NIGHT SHIFT
---------------------------------------------------
The coordination database is at: /workspace/icu_hive.db

STEP 1 — RECORD CURRENT SHIFT STATE (Facts)
Record the following facts into the coordination store.
All timestamps should be the current Unix time (use date +%s or equivalent).

  a) Key: icu.medication_round
     Value: current Unix timestamp (as a string)
     TTL: 3600 seconds
     Source tag: night-shift-intake

  b) Key: icu.ventilator_check
     Value: current Unix timestamp (as a string)
     TTL: 1800 seconds
     Source tag: night-shift-intake

  c) Key: icu.patient_census
     Value: "14"
     TTL: 7200 seconds
     Source tag: night-shift-intake

  d) Key: icu.code_blue_protocol
     Value: "active"
     (No TTL — this fact must persist indefinitely)
     Source tag: night-shift-intake

STEP 2 — QUEUE INCOMING ALERTS
Queue the following alerts into the coordination system:

  a) Topic: equipment
     Message: "Defibrillator unit DEF-3 requires recalibration before 02:00"

  b) Topic: medication
     Message: "Insulin drip for patient Bed-7 needs reassessment at midnight"

  c) Topic: equipment
     Message: "Suction pump in Room 4 is making abnormal noise — inspect before use"

  d) Topic: staffing
     Message: "Dr. Okafor on-call for cardiac emergencies — contact ext 4471"

STEP 3 — CONSUME EQUIPMENT ALERTS
Pop (claim) ONLY the equipment-topic alerts so the night charge nurse
can act on them immediately. Other alerts must remain pending.

STEP 4 — CLAIM THE NIGHT SHIFT HANDOFF TASK
Claim a task named exactly: night-shift-handoff-2024-01-15
If the claim fails (someone else already has it), record that fact
and do NOT attempt to release it.
If the claim succeeds, release it with the result string:
"night shift coordination initialized — 14 patients on census"

STEP 5 — PURGE OLD ALERT RECORDS
Purge any claimed alerts that are older than 86400 seconds (24 hours).

STEP 6 — GENERATE SHIFT REPORT
Using the coordination system's stats command, generate a file named
shift_report.json in /workspace containing:
  - All fields returned by the stats command
  - An additional field "shift" with value "night"
  - An additional field "task_claimed" with boolean true if the task
    claim in Step 4 succeeded, false otherwise
  - An additional field "equipment_alerts_consumed" with the count of
    equipment alerts that were popped in Step 3

The file must be valid JSON.
================================================================
"""

write(f"{WORKSPACE}/shift_handoff_log.txt", handoff_log)

# ── 4. Distractor files ────────────────────────────────────────────────────────
write(f"{WORKSPACE}/config/monitoring/alert_thresholds.yaml", """\
# ICU Alert Thresholds Configuration
heart_rate:
  low: 45
  high: 130
spo2:
  low: 88
respiratory_rate:
  low: 8
  high: 30
blood_pressure:
  systolic_high: 180
  diastolic_high: 110
""")

write(f"{WORKSPACE}/config/monitoring/device_registry.json", json.dumps({
    "devices": [
        {"id": "VT-7", "type": "ventilator", "room": "ICU-A", "last_service": "2024-01-10"},
        {"id": "DEF-3", "type": "defibrillator", "room": "ICU-B", "last_service": "2023-12-15"},
        {"id": "IV-PUMP-12", "type": "iv_pump", "room": "ICU-C", "last_service": "2024-01-05"},
        {"id": "SUCTION-4", "type": "suction", "room": "ICU-D", "last_service": "2023-11-20"},
    ]
}, indent=2))

write(f"{WORKSPACE}/config/staff/night_roster.json", json.dumps({
    "shift": "night",
    "date": "2024-01-15",
    "staff": [
        {"name": "Nurse Chen", "role": "charge_nurse", "ext": "4201"},
        {"name": "Dr. Okafor", "role": "on_call_cardiac", "ext": "4471"},
        {"name": "Nurse Patel", "role": "floor_nurse", "ext": "4215"},
    ]
}, indent=2))

write(f"{WORKSPACE}/logs/day_shift_events.log", """\
[08:03] Patient Bed-2 admitted — cardiac monitoring initiated
[09:15] Ventilator VT-7 battery replaced
[10:30] Morning vitals completed — all within normal range
[11:45] IV pump calibration flagged — no technician available
[12:00] Medication round completed — morphine restocked
[13:20] Code blue protocol activated for Bed-11 — resolved
[14:00] X-ray rounds complete
[15:30] Insulin drip started for Bed-7
[16:45] Defibrillator DEF-3 calibration overdue — flagged for night shift
[17:00] Day shift ends — 14 patients on census
""")

write(f"{WORKSPACE}/logs/system_audit.log", """\
2024-01-14 22:00:01 INFO  coordination-store initialized
2024-01-14 22:00:02 INFO  morning-vitals-round claimed by day-shift-agent
2024-01-14 23:45:00 INFO  equipment-audit-stale claimed by crashed-agent-01
2024-01-15 06:30:00 ERROR crashed-agent-01 heartbeat lost
2024-01-15 08:00:00 INFO  day shift started
2024-01-15 17:00:00 INFO  day shift ended — handoff in progress
""")

write(f"{WORKSPACE}/protocols/code_blue.txt", """\
CODE BLUE PROTOCOL — ICU
========================
1. Announce code blue overhead
2. Assign roles: Compressor, Airway, IV/IO, Recorder, Team Lead
3. Begin CPR immediately — 30:2 ratio
4. Defibrillator to be available within 90 seconds
5. Document time of arrest and all interventions
6. Contact attending physician immediately
""")

write(f"{WORKSPACE}/protocols/medication_safety.txt", """\
MEDICATION SAFETY CHECKLIST
============================
- Verify 5 rights: Patient, Drug, Dose, Route, Time
- Double-check high-alert medications (insulin, heparin, morphine)
- Document in EMR within 15 minutes of administration
- Report discrepancies to charge nurse immediately
""")

write(f"{WORKSPACE}/memory/old_heartbeat_state.json", json.dumps({
    "last_email_check": 1705276800,
    "last_calendar_check": 1705276200,
    "last_weather_check": 1705274400,
    "note": "DEPRECATED — use coordination store instead"
}, indent=2))

write(f"{WORKSPACE}/memory/patient_summary_day.json", json.dumps({
    "census": 14,
    "critical": 3,
    "stable": 11,
    "pending_discharge": 1,
    "new_admissions_today": 2
}, indent=2))

write(f"{WORKSPACE}/scripts/legacy_state_writer.sh", """\
#!/bin/bash
# LEGACY — do not use
# This script used to write heartbeat-state.json
# It has been replaced by the coordination store
echo "WARNING: This script is deprecated" >&2
exit 1
""")

write(f"{WORKSPACE}/config/db_paths.conf", """\
# Database path configuration
# The active coordination database for this environment:
COORDINATION_DB=/workspace/icu_hive.db

# Legacy path (do not use):
# LEGACY_DB=/tmp/old_state.db
""")

write(f"{WORKSPACE}/docs/coordination_overview.md", """\
# ICU Multi-Agent Coordination System

This system uses a shared SQLite-backed store for coordinating between:
- Cron-based monitoring agents
- Interactive session agents
- Alert routing between shift handoffs

## Database Location
Active DB: /workspace/icu_hive.db

## Primitives
- Facts: short-lived key/value coordination state
- Alerts: cross-session notification queue
- Tasks: claim-based deduplication

See scripts/clankerhive.py for the implementation.
""")

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}")