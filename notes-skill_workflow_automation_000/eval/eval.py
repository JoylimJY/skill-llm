import sys
import json
import sqlite3
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
HOME = Path("/root")
DB_PATH = HOME / ".openclaw" / "workspace" / "notes" / "notes.db"
BACKUP_DIR = HOME / ".openclaw" / "workspace" / "notes" / "backups"

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ---- CHECK 1: DB was initialized and exists ----
try:
    db_exists = DB_PATH.exists()
    add_check(
        "db_initialized",
        db_exists,
        f"notes.db found at {DB_PATH}" if db_exists else f"notes.db NOT found at {DB_PATH}"
    )
except Exception as e:
    add_check("db_initialized", False, f"Exception: {e}")

# ---- CHECK 2: Notes table has correct schema ----
try:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
    table_exists = cur.fetchone() is not None
    add_check(
        "notes_table_exists",
        table_exists,
        "notes table exists" if table_exists else "notes table NOT found"
    )
except Exception as e:
    add_check("notes_table_exists", False, f"Exception: {e}")
    conn = None

# ---- CHECK 3: At least 4 notes were inserted (one per raw note) ----
try:
    cur.execute("SELECT COUNT(*) as cnt FROM notes")
    row = cur.fetchone()
    note_count = row[0]
    passed = note_count >= 4
    add_check(
        "notes_count_at_least_4",
        passed,
        f"Found {note_count} notes, expected >= 4"
    )
except Exception as e:
    add_check("notes_count_at_least_4", False, f"Exception: {e}")

# ---- CHECK 4: Content optimization was applied ----
# Notes should NOT be raw verbatim copies; they must have improvements:
# - Typos fixed: "radom" -> "random", "accuarcy" -> "accuracy", "memeory" -> "memory", "accumlation" -> "accumulation"
# - Content should be meaningfully expanded/structured (not just a 1:1 copy)
try:
    cur.execute("SELECT content FROM notes ORDER BY id ASC")
    all_notes = [row[0] for row in cur.fetchall()]
    
    # Check note 1: should not contain obvious raw typos
    note1_raw_typos = ["radom", "accuarcy"]
    note1_content = all_notes[0] if len(all_notes) >= 1 else ""
    typos_fixed_note1 = not any(t in note1_content for t in note1_raw_typos)
    add_check(
        "note1_typos_fixed",
        typos_fixed_note1,
        f"Note 1 content: {note1_content[:120]!r}. Raw typos {'absent (good)' if typos_fixed_note1 else 'still present (bad)'}"
    )
    
    # Check note 3: should not contain "memeory" or "accumlation"
    note3_raw_typos = ["memeory", "accumlation"]
    note3_content = all_notes[2] if len(all_notes) >= 3 else ""
    typos_fixed_note3 = not any(t in note3_content for t in note3_raw_typos)
    add_check(
        "note3_typos_fixed",
        typos_fixed_note3,
        f"Note 3 content: {note3_content[:120]!r}. Raw typos {'absent (good)' if typos_fixed_note3 else 'still present (bad)'}"
    )

    # Check note 4: should not contain "踩坑" raw run-on or missing punctuation (heuristic: length >= original)
    note4_content = all_notes[3] if len(all_notes) >= 4 else ""
    note4_meaningful = len(note4_content) >= 30  # at minimum it was stored
    add_check(
        "note4_stored",
        note4_meaningful,
        f"Note 4 content length: {len(note4_content)}"
    )

except Exception as e:
    add_check("content_optimization", False, f"Exception reading notes: {e}")

# ---- CHECK 5: Notes 2 and 4 are archived (archived=1) ----
try:
    cur.execute("SELECT id, archived FROM notes ORDER BY id ASC")
    notes_arch = {row[0]: row[1] for row in cur.fetchall()}
    
    # IDs 2 and 4 should be archived
    id2_archived = notes_arch.get(2, 0) == 1
    id4_archived = notes_arch.get(4, 0) == 1
    both_archived = id2_archived and id4_archived
    add_check(
        "notes_2_and_4_archived",
        both_archived,
        f"Note 2 archived={notes_arch.get(2, 'missing')}, Note 4 archived={notes_arch.get(4, 'missing')}"
    )
    
    # Notes 1 and 3 should NOT be archived
    id1_not_archived = notes_arch.get(1, 0) == 0
    id3_not_archived = notes_arch.get(3, 0) == 0
    others_not_archived = id1_not_archived and id3_not_archived
    add_check(
        "notes_1_and_3_not_archived",
        others_not_archived,
        f"Note 1 archived={notes_arch.get(1, 'missing')}, Note 3 archived={notes_arch.get(3, 'missing')}"
    )
except Exception as e:
    add_check("archive_check", False, f"Exception: {e}")

# ---- CHECK 6: Backup was created with retention=3 ----
try:
    backup_exists = BACKUP_DIR.exists()
    if backup_exists:
        backup_files = sorted(BACKUP_DIR.glob("notes_*.db"))
        backup_count = len(backup_files)
        # Exactly 1 backup should exist (only one was made, retention=3 so <=3)
        backup_made = backup_count >= 1
        retention_respected = backup_count <= 3
        add_check(
            "backup_created",
            backup_made,
            f"Found {backup_count} backup file(s) in {BACKUP_DIR}"
        )
        add_check(
            "backup_retention_3",
            retention_respected,
            f"Backup count {backup_count} <= 3 (retention=3): {'OK' if retention_respected else 'FAIL - too many backups kept'}"
        )
    else:
        add_check("backup_created", False, f"Backup directory {BACKUP_DIR} does not exist")
        add_check("backup_retention_3", False, "No backups found")
except Exception as e:
    add_check("backup_check", False, f"Exception: {e}")

if conn:
    conn.close()

# ---- Scoring ----
passed_checks = sum(1 for c in checks if c["passed"])
total_checks = len(checks)
score = round(passed_checks / total_checks, 3) if total_checks > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))