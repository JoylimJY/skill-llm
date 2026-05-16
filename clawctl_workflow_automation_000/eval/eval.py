import subprocess
import json
import sys
import os
import sqlite3
from pathlib import Path

def run(cmd, env=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def get_db_path():
    return os.path.expanduser("~/.openclaw/clawctl.db")

def query_db(db_path, sql, params=()):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        return []

checks = []
score_total = 0
score_max = 0

def add_check(name, passed, detail, weight=1):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score_total, score_max
    score_max += weight
    if passed:
        score_total += weight

db_path = get_db_path()

# ── CHECK 1: DB initialized ──────────────────────────────────────────────────
db_exists = Path(db_path).exists()
add_check("DB initialized", db_exists,
          f"DB at {db_path} {'exists' if db_exists else 'NOT FOUND'}", weight=2)

if not db_exists:
    print(json.dumps({
        "passed": False,
        "score": 0.0,
        "checks": checks + [{"name": "FATAL", "passed": False, "detail": "DB missing, aborting eval"}]
    }))
    sys.exit(0)

# ── CHECK 2: All 5 agents registered ─────────────────────────────────────────
agents_rows = query_db(db_path, "SELECT name, role FROM agents")
agent_names = {r["name"] for r in agents_rows}
required_agents = {"screener", "docker_agent", "admet_agent", "reporter", "lead_coord"}
missing_agents = required_agents - agent_names
add_check("All 5 agents registered",
          len(missing_agents) == 0,
          f"Registered: {sorted(agent_names)}. Missing: {sorted(missing_agents)}", weight=3)

# ── CHECK 3: Agent roles assigned correctly ───────────────────────────────────
agent_role_map = {r["name"]: r["role"] for r in agents_rows}
expected_roles = {
    "screener": "screening-agent",
    "docker_agent": "docking-agent",
    "admet_agent": "admet-agent",
    "reporter": "reporting-agent",
}
role_ok = all(agent_role_map.get(a) == r for a, r in expected_roles.items())
add_check("Agent roles correctly assigned",
          role_ok,
          f"Roles found: {agent_role_map}", weight=2)

# ── CHECK 4: All 4 tasks created ─────────────────────────────────────────────
tasks_rows = query_db(db_path, "SELECT id, subject, priority, owner, status, parent_id FROM tasks")
task_subjects = [r["subject"] for r in tasks_rows]

expected_subjects = [
    "Screen batch_002 compounds against target EGFR",
    "Dock top hits from batch_002 into EGFR binding pocket",
    "Run ADMET profiling on docked compounds",
    "Compile lead optimization report for Sprint 3",
]
found_subjects = []
for es in expected_subjects:
    found = any(es.lower() in s.lower() for s in task_subjects)
    found_subjects.append(found)

all_tasks_created = all(found_subjects)
add_check("All 4 tasks created",
          all_tasks_created,
          f"Expected subjects found: {list(zip([s[:30] for s in expected_subjects], found_subjects))}", weight=3)

# ── CHECK 5: Priority assignments ─────────────────────────────────────────────
# TASK_A priority=2, TASK_B=1, TASK_C=1, TASK_D=0
def find_task(keyword):
    for r in tasks_rows:
        if keyword.lower() in r["subject"].lower():
            return r
    return None

task_a = find_task("Screen batch_002")
task_b = find_task("Dock top hits")
task_c = find_task("ADMET profiling")
task_d = find_task("Compile lead")

priority_ok = (
    task_a is not None and task_a["priority"] == 2 and
    task_b is not None and task_b["priority"] == 1 and
    task_c is not None and task_c["priority"] == 1 and
    task_d is not None and task_d["priority"] == 0
)
prio_detail = {
    "task_a_priority": task_a["priority"] if task_a else "NOT FOUND",
    "task_b_priority": task_b["priority"] if task_b else "NOT FOUND",
    "task_c_priority": task_c["priority"] if task_c else "NOT FOUND",
    "task_d_priority": task_d["priority"] if task_d else "NOT FOUND",
}
add_check("Task priorities correctly set", priority_ok, str(prio_detail), weight=2)

# ── CHECK 6: Parent-child relationships ───────────────────────────────────────
# TASK_B.parent = TASK_A, TASK_C.parent = TASK_B, TASK_D.parent = TASK_C
parent_ok = False
if task_a and task_b and task_c and task_d:
    parent_ok = (
        task_b["parent_id"] == task_a["id"] and
        task_c["parent_id"] == task_b["id"] and
        task_d["parent_id"] == task_c["id"]
    )
add_check("Task parent-child chain correct",
          parent_ok,
          f"B.parent={task_b['parent_id'] if task_b else '?'} (want {task_a['id'] if task_a else '?'}), "
          f"C.parent={task_c['parent_id'] if task_c else '?'} (want {task_b['id'] if task_b else '?'}), "
          f"D.parent={task_d['parent_id'] if task_d else '?'} (want {task_c['id'] if task_c else '?'})",
          weight=3)

# ── CHECK 7: Task assignments (owner/for) ────────────────────────────────────
assign_ok = (
    task_a is not None and task_a.get("owner") == "screener" and
    task_b is not None and task_b.get("owner") == "docker_agent" and
    task_c is not None and task_c.get("owner") == "admet_agent" and
    task_d is not None and task_d.get("owner") == "reporter"
)
add_check("Tasks assigned to correct agents",
          assign_ok,
          f"Owners: A={task_a.get('owner') if task_a else '?'}, "
          f"B={task_b.get('owner') if task_b else '?'}, "
          f"C={task_c.get('owner') if task_c else '?'}, "
          f"D={task_d.get('owner') if task_d else '?'}",
          weight=2)

# ── CHECK 8: All tasks ended as done ──────────────────────────────────────────
all_done = all(
    t is not None and t["status"] == "done"
    for t in [task_a, task_b, task_c, task_d]
)
status_detail = {
    "A": task_a["status"] if task_a else "?",
    "B": task_b["status"] if task_b else "?",
    "C": task_c["status"] if task_c else "?",
    "D": task_d["status"] if task_d else "?",
}
add_check("All tasks completed (status=done)", all_done, str(status_detail), weight=3)

# ── CHECK 9: TASK_B was blocked by TASK_A ─────────────────────────────────────
# Check activity log or events for a 'block' event on task_b referencing task_a
block_rows = query_db(db_path,
    "SELECT * FROM events WHERE type='block' OR verb='block' OR event_type='block'")
# Try broader: look for any event referencing both task_b and task_a with block semantics
# clawctl stores events in a feed/activity table — try common table names
all_tables = query_db(db_path, "SELECT name FROM sqlite_master WHERE type='table'")
table_names = [t["name"] for t in all_tables]

block_found = False
block_detail = f"Tables: {table_names}"

# Search across all tables for blocking evidence
for tname in table_names:
    try:
        rows = query_db(db_path, f"SELECT * FROM {tname}")
        for row in rows:
            row_str = str(row).lower()
            if "block" in row_str and (
                str(task_b["id"]) in row_str if task_b else False
            ):
                block_found = True
                block_detail = f"Block event found in table '{tname}': {row}"
                break
        if block_found:
            break
    except Exception:
        pass

add_check("TASK_B was blocked (waiting for TASK_A)", block_found,
          block_detail, weight=2)

# ── CHECK 10: Completion notes on tasks ──────────────────────────────────────
# Check that done events have meaningful notes
notes_rows = []
for tname in table_names:
    try:
        cols = query_db(db_path, f"PRAGMA table_info({tname})")
        col_names = [c["name"] for c in cols]
        if any(c in col_names for c in ["note", "message", "body", "notes"]):
            note_col = next(c for c in ["note", "message", "body", "notes"] if c in col_names)
            rows = query_db(db_path, f"SELECT {note_col} FROM {tname} WHERE {note_col} IS NOT NULL AND {note_col} != ''")
            notes_rows.extend(rows)
    except Exception:
        pass

# Look for specific note content
screening_note_found = any(
    "18 hits" in str(r).lower() or "screening" in str(r).lower() or "threshold" in str(r).lower()
    for r in notes_rows
)
docking_note_found = any(
    "docking" in str(r).lower() or "kcal" in str(r).lower() or "scored" in str(r).lower()
    for r in notes_rows
)
notes_ok = screening_note_found and docking_note_found
add_check("Completion notes recorded on tasks",
          notes_ok,
          f"Screening note: {screening_note_found}, Docking note: {docking_note_found}. "
          f"Sample notes found: {[str(r)[:80] for r in notes_rows[:4]]}",
          weight=2)

# ── CHECK 11: Handoff messages sent (type=handoff) ────────────────────────────
msg_rows = []
for tname in table_names:
    try:
        cols = query_db(db_path, f"PRAGMA table_info({tname})")
        col_names = [c["name"] for c in cols]
        if "type" in col_names and any(c in col_names for c in ["body", "content", "message"]):
            body_col = next(c for c in ["body", "content", "message"] if c in col_names)
            rows = query_db(db_path, f"SELECT type, {body_col}, sender, recipient FROM {tname}")
            msg_rows.extend(rows)
    except Exception:
        pass

handoff_msgs = [r for r in msg_rows if str(r.get("type", "")).lower() == "handoff"]
handoff_count = len(handoff_msgs)

# Expect at least 2 handoff messages (screener→docker_agent, admet_agent→reporter)
handoffs_ok = handoff_count >= 2
add_check("At least 2 handoff-typed messages sent",
          handoffs_ok,
          f"Handoff messages found: {handoff_count}. Details: {[str(h)[:100] for h in handoff_msgs[:3]]}",
          weight=3)

# ── CHECK 12: Broadcast message sent by lead_coord ────────────────────────────
broadcast_found = False
broadcast_detail = "No broadcast found"
for tname in table_names:
    try:
        cols = query_db(db_path, f"PRAGMA table_info({tname})")
        col_names = [c["name"] for c in cols]
        rows = query_db(db_path, f"SELECT * FROM {tname}")
        for row in rows:
            row_str = str(row).lower()
            if "sprint 3 docking phase" in row_str or (
                "broadcast" in row_str and "lead_coord" in row_str
            ) or (
                "lead_coord" in row_str and "admet" in row_str
            ):
                broadcast_found = True
                broadcast_detail = f"Broadcast found in '{tname}': {str(row)[:150]}"
                break
        if broadcast_found:
            break
    except Exception:
        pass

add_check("Broadcast message sent by lead_coord", broadcast_found, broadcast_detail, weight=2)

# ── CHECK 13: Meta/artifact references attached ────────────────────────────────
# Check that artifact paths are stored in meta fields
artifact_keywords = [
    "batch_002_hits",
    "batch_002_docked",
    "batch_002_flags",
    "sprint3_leads",
]
meta_found = {kw: False for kw in artifact_keywords}
for tname in table_names:
    try:
        rows = query_db(db_path, f"SELECT * FROM {tname}")
        for row in rows:
            row_str = str(row)
            for kw in artifact_keywords:
                if kw in row_str:
                    meta_found[kw] = True
    except Exception:
        pass

meta_ok = sum(meta_found.values()) >= 2
add_check("Artifact metadata attached to tasks (≥2 artifacts)",
          meta_ok,
          f"Artifacts found: {meta_found}", weight=2)

# ── CHECK 14: TASK_D was linked to reporter and completed ─────────────────────
reporter_done = (
    task_d is not None and
    task_d["status"] == "done" and
    task_d.get("owner") == "reporter"
)
add_check("Reporter completed TASK_D (report compilation)",
          reporter_done,
          f"task_d status={task_d['status'] if task_d else '?'}, owner={task_d.get('owner') if task_d else '?'}",
          weight=2)

# ── FINAL SCORE ───────────────────────────────────────────────────────────────
final_score = round(score_total / score_max, 3) if score_max > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}, indent=2))