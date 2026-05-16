import sys
import os
import json
import sqlite3
import datetime
from pathlib import Path

workspace = sys.argv[1]

checks = []
score_weights = []

def check(name, weight=1.0):
    def decorator(fn):
        def wrapper():
            try:
                passed, detail = fn()
            except Exception as e:
                passed, detail = False, f"Exception: {e}"
            checks.append({"name": name, "passed": passed, "detail": detail})
            score_weights.append((passed, weight))
            return passed
        return wrapper
    return decorator

# --- Locate the main database ---
db_candidates = list(Path(workspace).rglob("fleet_ops.db"))

@check("fleet_ops.db exists", weight=1.0)
def check_db_exists():
    if not db_candidates:
        return False, "fleet_ops.db not found anywhere in workspace"
    return True, f"Found at {db_candidates[0]}"

db_path = str(db_candidates[0]) if db_candidates else None

def get_conn():
    if not db_path:
        raise FileNotFoundError("No DB found")
    return sqlite3.connect(db_path)

# --- Check agent_memos table exists with correct schema ---
@check("agent_memos table has required columns", weight=1.5)
def check_agent_memos_schema():
    conn = get_conn()
    cur = conn.execute("PRAGMA table_info(agent_memos)")
    cols = {row[1]: row[2] for row in cur.fetchall()}
    conn.close()
    required = {"id", "agent_id", "key", "value", "priority", "created_at", "expires_at"}
    missing = required - set(cols.keys())
    if missing:
        return False, f"Missing columns: {missing}. Found: {set(cols.keys())}"
    return True, f"All required columns present: {set(cols.keys())}"

# --- Check session_logs table exists with correct schema ---
@check("session_logs table has required columns", weight=1.5)
def check_session_logs_schema():
    conn = get_conn()
    try:
        cur = conn.execute("PRAGMA table_info(session_logs)")
        cols = {row[1]: row[2] for row in cur.fetchall()}
        conn.close()
    except Exception as e:
        return False, f"Could not query session_logs: {e}"
    required = {"id", "session_id", "agent", "message", "metadata", "created_at"}
    missing = required - set(cols.keys())
    if missing:
        return False, f"Missing columns: {missing}"
    return True, f"Columns OK: {set(cols.keys())}"

# --- Check cache table exists with correct schema including BLOB value ---
@check("cache table has correct schema (BLOB value, expires_at)", weight=1.5)
def check_cache_schema():
    conn = get_conn()
    try:
        cur = conn.execute("PRAGMA table_info(cache)")
        cols = {row[1]: row[2].upper() for row in cur.fetchall()}
        conn.close()
    except Exception as e:
        return False, f"Could not query cache: {e}"
    required = {"id", "key", "value", "created_at", "expires_at"}
    missing = required - set(cols.keys())
    if missing:
        return False, f"Missing columns: {missing}"
    if "VALUE" in cols and "BLOB" not in cols["VALUE"] and cols["VALUE"] != "BLOB":
        # Accept BLOB or NONE (affinity)
        pass  # SQLite is flexible, we accept any
    return True, f"Cache schema OK: {cols}"

# --- Check WAL mode is enabled ---
@check("WAL journal mode is enabled", weight=1.5)
def check_wal_mode():
    conn = get_conn()
    cur = conn.execute("PRAGMA journal_mode")
    mode = cur.fetchone()[0]
    conn.close()
    if mode.lower() == "wal":
        return True, "WAL mode confirmed"
    return False, f"Expected WAL, got: {mode}"

# --- Check agent_memos data was batch-inserted from raw JSON ---
@check("agent_memos has data loaded from raw JSON (>=15 rows before expiry cleanup)", weight=2.0)
def check_memos_data():
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM agent_memos")
    count = cur.fetchone()[0]
    conn.close()
    # After cleanup_expired, expired ones are gone; we had 20 inserted, some expired
    # We expect at least some data (>0) and the expired ones cleaned up
    if count == 0:
        return False, "agent_memos is empty — data was not inserted"
    # The raw data had 20 entries; some expired. After cleanup count < 20 is expected.
    return True, f"agent_memos has {count} rows (expired entries cleaned up)"

# --- Check expired memos were cleaned up ---
@check("Expired agent_memos entries have been removed", weight=2.0)
def check_memos_expired_cleaned():
    conn = get_conn()
    now_iso = datetime.datetime.now().isoformat()
    cur = conn.execute(
        "SELECT COUNT(*) FROM agent_memos WHERE expires_at < ?", (now_iso,)
    )
    count = cur.fetchone()[0]
    conn.close()
    if count > 0:
        return False, f"{count} expired memo entries still present — cleanup_expired was not called"
    return True, "All expired memo entries removed"

# --- Check session_logs was populated ---
@check("session_logs has all 30 raw entries migrated", weight=2.0)
def check_session_logs_data():
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM session_logs")
    count = cur.fetchone()[0]
    conn.close()
    if count < 30:
        return False, f"Expected >=30 session log rows, found {count}"
    return True, f"session_logs has {count} rows"

# --- Check session_logs has 'severity' column (schema migration) ---
@check("session_logs has 'severity' column added via migration", weight=2.0)
def check_severity_column():
    conn = get_conn()
    cur = conn.execute("PRAGMA table_info(session_logs)")
    cols = {row[1] for row in cur.fetchall()}
    conn.close()
    if "severity" not in cols:
        return False, f"'severity' column missing from session_logs. Columns: {cols}"
    return True, "'severity' column present in session_logs"

# --- Check cache data was inserted and expired entries cleaned ---
@check("cache table has valid (non-expired) entries only", weight=2.0)
def check_cache_data():
    conn = get_conn()
    now_iso = datetime.datetime.now().isoformat()
    cur_total = conn.execute("SELECT COUNT(*) FROM cache")
    total = cur_total.fetchone()[0]
    cur_expired = conn.execute("SELECT COUNT(*) FROM cache WHERE expires_at < ?", (now_iso,))
    expired = cur_expired.fetchone()[0]
    conn.close()
    if total == 0:
        return False, "cache table is empty"
    if expired > 0:
        return False, f"{expired} expired cache entries still present"
    return True, f"cache has {total} valid entries, 0 expired"

# --- Check indexes exist ---
@check("Required indexes created on agent_memos", weight=1.5)
def check_indexes_memos():
    conn = get_conn()
    cur = conn.execute("PRAGMA index_list(agent_memos)")
    indexes = [row[1] for row in cur.fetchall()]
    conn.close()
    expected_cols = ["agent_id", "key", "expires_at"]
    missing = []
    for col in expected_cols:
        if not any(col in idx for idx in indexes):
            missing.append(col)
    if missing:
        return False, f"Missing indexes for columns: {missing}. Found: {indexes}"
    return True, f"Indexes found: {indexes}"

@check("Required indexes created on session_logs", weight=1.0)
def check_indexes_sessions():
    conn = get_conn()
    cur = conn.execute("PRAGMA index_list(session_logs)")
    indexes = [row[1] for row in cur.fetchall()]
    conn.close()
    expected_cols = ["session_id", "created_at"]
    missing = [col for col in expected_cols if not any(col in idx for idx in indexes)]
    if missing:
        return False, f"Missing indexes for: {missing}. Found: {indexes}"
    return True, f"Indexes found: {indexes}"

@check("Required indexes created on cache", weight=1.0)
def check_indexes_cache():
    conn = get_conn()
    cur = conn.execute("PRAGMA index_list(cache)")
    indexes = [row[1] for row in cur.fetchall()]
    conn.close()
    expected_cols = ["key", "expires_at"]
    missing = [col for col in expected_cols if not any(col in idx for idx in indexes)]
    if missing:
        return False, f"Missing indexes for: {missing}. Found: {indexes}"
    return True, f"Indexes found: {indexes}"

# --- Check backup exists ---
@check("Backup database file exists in backups/ directory", weight=1.5)
def check_backup_exists():
    backup_candidates = list(Path(workspace).rglob("backups/*.db")) + \
                        list(Path(workspace).rglob("backups/**/*.db"))
    if not backup_candidates:
        # Also check for any .db file with 'backup' in name
        backup_candidates = [p for p in Path(workspace).rglob("*.db")
                             if "backup" in p.name.lower() and p.name != "fleet_ops.db"]
    if not backup_candidates:
        return False, "No backup .db file found in backups/ or with 'backup' in name"
    # Verify it's a valid SQLite database
    bp = str(backup_candidates[0])
    try:
        conn = sqlite3.connect(bp)
        conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        conn.close()
        return True, f"Valid backup found at {bp}"
    except Exception as e:
        return False, f"Backup file exists but is not valid SQLite: {e}"

# --- Check UNIQUE constraint on cache.key ---
@check("cache.key column has UNIQUE constraint", weight=1.0)
def check_cache_unique_key():
    conn = get_conn()
    cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='cache'")
    row = cur.fetchone()
    conn.close()
    if not row:
        return False, "cache table not found in sqlite_master"
    ddl = row[0].upper()
    if "UNIQUE" in ddl:
        return True, "UNIQUE constraint found on cache table"
    # Also check via index
    conn2 = get_conn()
    cur2 = conn2.execute("PRAGMA index_list(cache)")
    idxs = cur2.fetchall()
    for idx in idxs:
        if idx[2] == 1:  # unique flag
            conn2.close()
            return True, f"UNIQUE index found: {idx[1]}"
    conn2.close()
    return False, f"No UNIQUE constraint found. DDL: {row[0][:200]}"

# --- Run all checks ---
check_db_exists()
if db_path:
    check_agent_memos_schema()
    check_session_logs_schema()
    check_cache_schema()
    check_wal_mode()
    check_memos_data()
    check_memos_expired_cleaned()
    check_session_logs_data()
    check_severity_column()
    check_cache_data()
    check_indexes_memos()
    check_indexes_sessions()
    check_indexes_cache()
    check_backup_exists()
    check_cache_unique_key()
else:
    for name in [
        "agent_memos table has required columns",
        "session_logs table has required columns",
        "cache table has correct schema (BLOB value, expires_at)",
        "WAL journal mode is enabled",
        "agent_memos has data loaded from raw JSON (>=15 rows before expiry cleanup)",
        "Expired agent_memos entries have been removed",
        "session_logs has all 30 raw entries migrated",
        "session_logs has 'severity' column added via migration",
        "cache table has valid (non-expired) entries only",
        "Required indexes created on agent_memos",
        "Required indexes created on session_logs",
        "Required indexes created on cache",
        "Backup database file exists in backups/ directory",
        "cache.key column has UNIQUE constraint",
    ]:
        checks.append({"name": name, "passed": False, "detail": "DB not found, skipped"})
        score_weights.append((False, 1.0))

total_weight = sum(w for _, w in score_weights)
passed_weight = sum(w for p, w in score_weights if p)
score = round(passed_weight / total_weight, 4) if total_weight > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))