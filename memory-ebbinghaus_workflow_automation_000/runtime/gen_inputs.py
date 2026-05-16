import os
import json
import random
import math
from pathlib import Path
from datetime import datetime, timedelta, timezone

random.seed(42)

workspace = Path("/workspace")

# ── Create realistic distractor directory structure ──────────────────────────
dirs = [
    "research/compounds/batch_A",
    "research/compounds/batch_B",
    "research/trials/phase1",
    "research/trials/phase2",
    "reports/quarterly/Q1",
    "reports/quarterly/Q2",
    "scripts",
    "logs/2024",
    "logs/2023",
    "config",
    "archive/old_reports",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "research/compounds/batch_A/compound_log.csv": "id,name,mw,activity\n1,CPD-001,342.4,high\n2,CPD-002,198.2,low\n",
    "research/compounds/batch_B/screening_results.txt": "Batch B screening: 14/20 active\nDate: 2024-03-15\n",
    "research/trials/phase1/enrollment.json": json.dumps({"trial_id": "T-2024-01", "enrolled": 45, "target": 60}),
    "research/trials/phase2/protocol_v2.txt": "Phase 2 protocol: Double-blind, placebo-controlled\nDuration: 6 months\n",
    "reports/quarterly/Q1/summary.txt": "Q1 Research Summary\nActive compounds: 23\nNew leads: 5\n",
    "reports/quarterly/Q2/summary.txt": "Q2 Research Summary\nActive compounds: 19\nNew leads: 3\n",
    "logs/2024/system.log": "2024-01-10 09:00:00 INFO System started\n2024-01-10 09:01:00 INFO DB connected\n",
    "logs/2023/system.log": "2023-12-31 23:59:00 INFO Year-end checkpoint\n",
    "config/pipeline_config.yaml": "pipeline:\n  steps: [ingest, clean, analyze]\n  output_format: parquet\n",
    "archive/old_reports/report_2022.txt": "Legacy report from 2022. Superseded.\n",
    "research/notes.txt": "General research observations - Q3 2024\nSee trial logs for details.\n",
    "reports/audit_checklist.txt": "Quarterly audit checklist:\n[ ] Data integrity\n[ ] Access logs\n[ ] Knowledge base review\n",
}
for rel_path, content in distractor_files.items():
    (workspace / rel_path).write_text(content)

# ── Install the ebbinghaus script ─────────────────────────────────────────────
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

ebbinghaus_script = r'''#!/usr/bin/env python3
"""Ebbinghaus forgetting curve memory lifecycle manager."""

import json
import math
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("EBBINGHAUS_DB", "./memory_db.json"))
ARCHIVE_PATH = Path(os.environ.get("EBBINGHAUS_ARCHIVE", "./MEMORY.md"))

STATUS_ACTIVE  = "active"
STATUS_ARCHIVE = "archived"


def load_db():
    if not DB_PATH.exists():
        db = {"memories": [], "next_id": 1}
        save_db(db)
        return db
    with open(DB_PATH) as f:
        return json.load(f)


def save_db(db):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)


def compute_strength(last_reviewed_iso: str, stability: float) -> float:
    last = datetime.fromisoformat(last_reviewed_iso)
    now  = datetime.now(timezone.utc)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    days = (now - last).total_seconds() / 86400
    return math.exp(-days / stability)


def strength_label(s: float) -> str:
    if s >= 0.7:
        return "🟢 Active"
    elif s >= 0.3:
        return "🟡 Decaying"
    else:
        return "🔴 Fading"


def cmd_status(args):
    db = load_db()
    memories = [m for m in db["memories"] if m.get("status", STATUS_ACTIVE) == STATUS_ACTIVE]
    if not memories:
        print("No active memory items.")
        return
    print(f"{'ID':<6} {'Strength':<10} {'Status':<16} {'Category':<12} {'Content'}")
    print("-" * 80)
    for m in memories:
        s = compute_strength(m["last_reviewed"], m["stability"])
        print(f"{m['id']:<6} {s:<10.4f} {strength_label(s):<16} {m.get('category','general'):<12} {m['content'][:60]}")


def cmd_decay(args):
    db = load_db()
    updated = 0
    for m in db["memories"]:
        if m.get("status", STATUS_ACTIVE) == STATUS_ACTIVE:
            m["strength"] = compute_strength(m["last_reviewed"], m["stability"])
            updated += 1
    save_db(db)
    print(f"Decay recalculated for {updated} active items.")


def cmd_add(args):
    db = load_db()
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "id": db["next_id"],
        "content": args.content,
        "category": args.category or "general",
        "source": args.source or "manual",
        "created_at": now,
        "last_reviewed": now,
        "stability": 1.0,
        "strength": 1.0,
        "review_count": 0,
        "status": STATUS_ACTIVE,
    }
    db["memories"].append(item)
    db["next_id"] += 1
    save_db(db)
    print(f"Added memory item #{item['id']}: {item['content'][:60]}")


def cmd_review(args):
    db = load_db()
    for m in db["memories"]:
        if m["id"] == args.id and m.get("status", STATUS_ACTIVE) == STATUS_ACTIVE:
            m["last_reviewed"] = datetime.now(timezone.utc).isoformat()
            m["stability"] = round(m["stability"] * 1.5, 6)
            m["strength"] = 1.0
            m["review_count"] = m.get("review_count", 0) + 1
            save_db(db)
            print(f"Reviewed #{args.id}. New stability: {m['stability']:.4f}")
            return
    print(f"Memory #{args.id} not found or not active.")


def cmd_forget(args):
    db = load_db()
    before = len(db["memories"])
    db["memories"] = [m for m in db["memories"] if m["id"] != args.id]
    if len(db["memories"]) < before:
        save_db(db)
        print(f"Deleted memory #{args.id}.")
    else:
        print(f"Memory #{args.id} not found.")


def cmd_archive(args):
    db = load_db()
    for m in db["memories"]:
        if m["id"] == args.id and m.get("status", STATUS_ACTIVE) == STATUS_ACTIVE:
            m["status"] = STATUS_ARCHIVE
            save_db(db)
            # Append to MEMORY.md
            ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(ARCHIVE_PATH, "a") as f:
                f.write(f"\n## [{m['id']}] {m['content']}\n")
                f.write(f"- Category: {m.get('category','general')}\n")
                f.write(f"- Source: {m.get('source','manual')}\n")
                f.write(f"- Archived: {datetime.now(timezone.utc).isoformat()}\n")
            print(f"Archived memory #{args.id} to {ARCHIVE_PATH}.")
            return
    print(f"Memory #{args.id} not found or not active.")


def cmd_heartbeat(args):
    db = load_db()
    memories = [m for m in db["memories"] if m.get("status", STATUS_ACTIVE) == STATUS_ACTIVE]
    fading  = []
    decaying = []
    for m in memories:
        s = compute_strength(m["last_reviewed"], m["stability"])
        if s < 0.3:
            fading.append(m)
        elif s < 0.7:
            decaying.append(m)
    if fading:
        print("⚠️  ATTENTION REQUIRED: The following memories are 🔴 Fading:")
        for m in fading:
            s = compute_strength(m["last_reviewed"], m["stability"])
            print(f"  #{m['id']} [{m.get('category','general')}] {m['content'][:60]} (strength={s:.4f})")
        print("Action needed: review or forget these items.")
    elif decaying:
        # Silent log only
        for m in decaying:
            s = compute_strength(m["last_reviewed"], m["stability"])
            pass  # silent
    else:
        print("HEARTBEAT_OK")


def main():
    parser = argparse.ArgumentParser(description="Ebbinghaus Memory Manager")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status")
    sub.add_parser("decay")

    p_add = sub.add_parser("add")
    p_add.add_argument("content")
    p_add.add_argument("--category", default="general")
    p_add.add_argument("--source", default="manual")

    p_review = sub.add_parser("review")
    p_review.add_argument("id", type=int)

    p_forget = sub.add_parser("forget")
    p_forget.add_argument("id", type=int)

    p_archive = sub.add_parser("archive")
    p_archive.add_argument("id", type=int)

    sub.add_parser("heartbeat")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    dispatch = {
        "status":    cmd_status,
        "decay":     cmd_decay,
        "add":       cmd_add,
        "review":    cmd_review,
        "forget":    cmd_forget,
        "archive":   cmd_archive,
        "heartbeat": cmd_heartbeat,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
'''

(workspace / "scripts" / "ebbinghaus.py").write_text(ebbinghaus_script)

# ── Build a pre-populated memory_db.json with backdated timestamps ────────────
# We manually craft the DB so items are in specific decay states.
# Using fixed timestamps relative to "now" won't work perfectly for eval,
# so we use last_reviewed timestamps that are far enough in the past.

now = datetime.now(timezone.utc)

def make_timestamp(days_ago: float) -> str:
    return (now - timedelta(days=days_ago)).isoformat()

# Item 1: 🔴 Fading — last reviewed 15 days ago, stability=1.0
# strength = e^(-15/1.0) ≈ 3.06e-7  (definitely fading)
item1 = {
    "id": 1,
    "content": "Compound CPD-417 shows strong binding affinity to target receptor TR-9",
    "category": "tech",
    "source": "lab_report_2024_q2",
    "created_at": make_timestamp(30),
    "last_reviewed": make_timestamp(15),
    "stability": 1.0,
    "strength": math.exp(-15 / 1.0),
    "review_count": 0,
    "status": "active",
}

# Item 2: 🔴 Fading — last reviewed 12 days ago, stability=1.5
# strength = e^(-12/1.5) ≈ e^(-8) ≈ 3.35e-4  (fading)
item2 = {
    "id": 2,
    "content": "Dr. Sarah Chen is the lead toxicologist for Phase 2 trial T-2024-01",
    "category": "person",
    "source": "team_directory",
    "created_at": make_timestamp(25),
    "last_reviewed": make_timestamp(12),
    "stability": 1.5,
    "strength": math.exp(-12 / 1.5),
    "review_count": 1,
    "status": "active",
}

# Item 3: 🔴 Fading — last reviewed 10 days ago, stability=1.0
# strength = e^(-10/1.0) ≈ 4.54e-5  (fading)
item3 = {
    "id": 3,
    "content": "Legacy solvent protocol SOP-2019-003 was deprecated in favor of SOP-2023-011",
    "category": "tech",
    "source": "sop_archive",
    "created_at": make_timestamp(60),
    "last_reviewed": make_timestamp(10),
    "stability": 1.0,
    "strength": math.exp(-10 / 1.0),
    "review_count": 0,
    "status": "active",
}

# Item 4: 🟡 Decaying — last reviewed 2 days ago, stability=2.0
# strength = e^(-2/2.0) = e^(-1) ≈ 0.368  (decaying, 0.3..0.7)
item4 = {
    "id": 4,
    "content": "FDA pre-IND meeting scheduled for 2024-09-15, requires submission package by 2024-08-01",
    "category": "event",
    "source": "calendar_sync",
    "created_at": make_timestamp(10),
    "last_reviewed": make_timestamp(2),
    "stability": 2.0,
    "strength": math.exp(-2 / 2.0),
    "review_count": 2,
    "status": "active",
}

# Item 5: 🟢 Active — last reviewed 0.1 days ago, stability=1.0
# strength = e^(-0.1/1.0) ≈ 0.905
item5 = {
    "id": 5,
    "content": "New HPLC calibration standard batch LOT-2024-0622 approved for use",
    "category": "tech",
    "source": "equipment_log",
    "created_at": make_timestamp(1),
    "last_reviewed": make_timestamp(0.1),
    "stability": 1.0,
    "strength": math.exp(-0.1 / 1.0),
    "review_count": 0,
    "status": "active",
}

db = {
    "memories": [item1, item2, item3, item4, item5],
    "next_id": 6,
}

db_path = workspace / "memory_db.json"
with open(db_path, "w") as f:
    json.dump(db, f, indent=2)

print("Workspace scaffold complete.")
print(f"  memory_db.json created with 5 items:")
print(f"    #1 🔴 Fading  - CPD-417 binding affinity (tech)")
print(f"    #2 🔴 Fading  - Dr. Sarah Chen (person)")
print(f"    #3 🔴 Fading  - Legacy SOP deprecated (tech)")
print(f"    #4 🟡 Decaying - FDA meeting (event)")
print(f"    #5 🟢 Active  - HPLC calibration (tech)")