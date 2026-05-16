import sys
import json
import sqlite3
import csv
from pathlib import Path
from datetime import datetime, timedelta

workspace = Path(sys.argv[1])

checks = []
score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ---- CHECK 1: Output file exists ----
report_path = workspace / "reports" / "association_report.json"
if not report_path.exists():
    # try rglob
    found = list(workspace.rglob("association_report.json"))
    if found:
        report_path = found[0]

try:
    assert report_path.exists(), "File not found"
    report = json.loads(report_path.read_text())
    score += add_check("output_file_exists", True, f"Found at {report_path}")
except Exception as e:
    add_check("output_file_exists", False, str(e))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ---- CHECK 2: Report has required top-level keys ----
required_keys = {"stats", "top_related_paper_001"}
try:
    missing = required_keys - set(report.keys())
    if missing:
        score += add_check("report_structure", False, f"Missing keys: {missing}")
    else:
        score += add_check("report_structure", True, "All required keys present")
except Exception as e:
    add_check("report_structure", False, str(e))

# ---- CHECK 3: Verify the engine was actually used (DB exists) ----
# The engine should have created a SQLite DB somewhere
db_candidates = list(Path.home().rglob("co_occurrence.db")) + list(workspace.rglob("co_occurrence.db"))
# Also check env var path
import os
env_db = os.environ.get("CO_OCCURRENCE_DB_PATH", "")
if env_db:
    db_candidates.append(Path(env_db))

db_path = None
for candidate in db_candidates:
    if candidate.exists():
        db_path = candidate
        break

try:
    assert db_path is not None, "No co_occurrence.db found"
    score += add_check("db_exists", True, f"Database found at {db_path}")
except Exception as e:
    add_check("db_exists", False, str(e))

# ---- CHECK 4: Verify data was loaded — edges exist in DB ----
try:
    assert db_path is not None
    conn = sqlite3.connect(str(db_path))
    total_edges = conn.execute("SELECT COUNT(*) FROM co_occurrence").fetchone()[0]
    # We expect at least some edges from recent sessions
    # After decay_old_edges(90), old edges should be removed
    # But recent edges for paper_001,paper_002,paper_003 should be present
    assert total_edges > 0, f"Database has 0 edges"
    score += add_check("db_has_edges", True, f"Database has {total_edges} edges")
except Exception as e:
    add_check("db_has_edges", False, str(e))

# ---- CHECK 5: Old edges were removed (decay_old_edges was called) ----
try:
    assert db_path is not None
    conn = sqlite3.connect(str(db_path))
    cutoff = (datetime.utcnow() - timedelta(days=90)).isoformat()
    old_edges = conn.execute(
        "SELECT COUNT(*) FROM co_occurrence WHERE last_updated < ?", (cutoff,)
    ).fetchone()[0]
    # After pruning, no edges should be older than 90 days
    if old_edges == 0:
        score += add_check("old_edges_pruned", True, "No stale edges (>90 days) remain in DB")
    else:
        add_check("old_edges_pruned", False, f"{old_edges} stale edges still present in DB — decay_old_edges(90) was not called or did not work")
except Exception as e:
    add_check("old_edges_pruned", False, str(e))

# ---- CHECK 6: Stats are correct ----
try:
    stats = report.get("stats", {})
    # After pruning old edges, total_edges should be less than the raw insert count
    # We know old sessions had: 5 unique pairs * ~3 records each = ~15 old edges
    # Recent edges: paper_001-paper_002, paper_001-paper_003, paper_002-paper_003 (15+1 PRIO times each = 16 records each)
    # paper_010-paper_020 (8+1=9), paper_001-paper_005 (5), paper_001-paper_007 (3), paper_001-paper_009 (2)
    # plus priority: paper_010-paper_015, paper_010-paper_020(already), paper_015-paper_020 (new from PRIO_002)
    # plus noise sessions (50-80 days old, NOT pruned)
    # We just check total_edges > 0 and < 100 (reasonable)
    total = stats.get("total_edges", -1)
    unique = stats.get("unique_memories", -1)
    avg_w = stats.get("avg_weight", -1)

    assert total > 0, f"total_edges={total} should be > 0"
    assert unique > 0, f"unique_memories={unique} should be > 0"
    assert avg_w > 0, f"avg_weight={avg_w} should be > 0"
    score += add_check("stats_valid", True, f"Stats: edges={total}, unique_memories={unique}, avg_weight={avg_w}")
except Exception as e:
    add_check("stats_valid", False, str(e))

# ---- CHECK 7: top_related_paper_001 is correctly populated ----
try:
    related = report.get("top_related_paper_001", [])
    assert isinstance(related, list), "top_related_paper_001 must be a list"
    assert len(related) > 0, "top_related_paper_001 is empty"
    assert len(related) <= 5, f"Expected top 5, got {len(related)}"

    # Extract IDs (handle both list-of-strings and list-of-dicts/lists)
    related_ids = []
    for item in related:
        if isinstance(item, str):
            related_ids.append(item)
        elif isinstance(item, (list, tuple)) and len(item) >= 1:
            related_ids.append(str(item[0]))
        elif isinstance(item, dict):
            # could be {"id": ..., "weight": ...} or {"memory_id": ...}
            for k in ["id", "memory_id", "paper_id", "name"]:
                if k in item:
                    related_ids.append(str(item[k]))
                    break

    # paper_002 and paper_003 should definitely be in top-5 for paper_001
    # (they were co-retrieved 15+1 PRIO = 16 times with paper_001 giving high weight)
    found_002 = any("paper_002" in rid for rid in related_ids)
    found_003 = any("paper_003" in rid for rid in related_ids)

    if found_002 and found_003:
        score += add_check("top_related_correct", True,
                           f"paper_002 and paper_003 both in top-5 for paper_001. IDs: {related_ids}")
    elif found_002 or found_003:
        # Partial credit
        score += 0.5 * 1.0
        add_check("top_related_correct", False,
                  f"Only partial: paper_002={found_002}, paper_003={found_003}. IDs: {related_ids}")
    else:
        add_check("top_related_correct", False,
                  f"Neither paper_002 nor paper_003 in top-5. Got: {related_ids}")
except Exception as e:
    add_check("top_related_correct", False, str(e))

# ---- CHECK 8: 3-paper sessions generate 3 edges (C(3,2)=3) ----
# paper_001-paper_002-paper_003 sessions mean all three pairs should be present
try:
    assert db_path is not None
    conn = sqlite3.connect(str(db_path))

    def get_weight(a, b):
        ca, cb = (a, b) if a <= b else (b, a)
        row = conn.execute(
            "SELECT weight FROM co_occurrence WHERE memory_a=? AND memory_b=?",
            (ca, cb)
        ).fetchone()
        return row[0] if row else None

    w_01_02 = get_weight("paper_001", "paper_002")
    w_01_03 = get_weight("paper_001", "paper_003")
    w_02_03 = get_weight("paper_002", "paper_003")

    assert w_01_02 is not None, "Edge paper_001-paper_002 missing"
    assert w_01_03 is not None, "Edge paper_001-paper_003 missing"
    assert w_02_03 is not None, "Edge paper_002-paper_003 missing (3-way session not generating C(3,2) edges)"

    # paper_001-paper_002 was in 15 sessions + 1 PRIO = 16 calls
    # paper_002-paper_003 was in 15 sessions + 1 PRIO = 16 calls (only via 3-paper sessions)
    # So weight for paper_002-paper_003 should be >= 15 (from 3-paper sessions only)
    assert w_02_03 >= 15.0, f"weight(paper_002, paper_003)={w_02_03} should be >=15, meaning 3-paper sessions were recorded correctly as C(3,2) pairs"

    score += add_check("three_way_sessions_correct", True,
                       f"3-paper sessions correctly expanded to 3 edges: w(01-02)={w_01_02}, w(01-03)={w_01_03}, w(02-03)={w_02_03}")
except Exception as e:
    add_check("three_way_sessions_correct", False, str(e))

# ---- CHECK 9: canonical pair ordering respected ----
try:
    assert db_path is not None
    conn = sqlite3.connect(str(db_path))
    # All stored pairs should have memory_a <= memory_b (lexicographic)
    bad_rows = conn.execute(
        "SELECT memory_a, memory_b FROM co_occurrence WHERE memory_a > memory_b LIMIT 5"
    ).fetchall()
    if len(bad_rows) == 0:
        score += add_check("canonical_pair_ordering", True, "All edges stored in canonical (lexicographic) order")
    else:
        add_check("canonical_pair_ordering", False, f"Found {len(bad_rows)} non-canonical pairs: {bad_rows[:3]}")
except Exception as e:
    add_check("canonical_pair_ordering", False, str(e))

# ---- Final Score ----
max_checks = 9
passed_checks = sum(1 for c in checks if c["passed"])
final_score = score / max_checks

print(json.dumps({
    "passed": final_score >= 0.7,
    "score": round(final_score, 3),
    "checks": checks
}, indent=2))