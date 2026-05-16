import os
import json
import random
import csv
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# --- Directory Structure ---
dirs = [
    "scripts",
    "data/raw_logs",
    "data/processed",
    "data/archive",
    "config",
    "reports",
    "notebooks",
    "tests",
    "logs",
    "docs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Create the CoOccurrenceEngine script (scripts/co_occurrence_tracker.py) ---
# This is the actual implementation the agent must use.
co_occurrence_tracker_code = '''
import sqlite3
import os
import math
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
from itertools import combinations


class CoOccurrenceEngine:
    """
    Hebbian co-occurrence graph engine.
    Records which memory IDs are retrieved together and computes association weights.
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.environ.get(
                "CO_OCCURRENCE_DB_PATH",
                str(Path.home() / ".config" / "cortexgraph" / "co_occurrence.db")
            )
        self.db_path = str(Path(db_path).expanduser())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        # Half-life in days for weight decay
        self.half_life_days = float(os.environ.get("CO_OCCURRENCE_HALF_LIFE_DAYS", "30"))

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS co_occurrence (
                    memory_a TEXT,
                    memory_b TEXT,
                    weight REAL DEFAULT 1.0,
                    last_updated TEXT,
                    created_at TEXT,
                    PRIMARY KEY (memory_a, memory_b)
                )
            """)
            conn.commit()

    def _canonical_pair(self, id_a: str, id_b: str) -> Tuple[str, str]:
        """Always store pairs in lexicographic order to avoid duplicates."""
        if id_a <= id_b:
            return (id_a, id_b)
        return (id_b, id_a)

    def _compute_decay_weight(self, current_weight: float, last_updated: str) -> float:
        """Apply exponential decay based on time since last update."""
        try:
            last_dt = datetime.fromisoformat(last_updated)
        except Exception:
            return current_weight
        delta_days = (datetime.utcnow() - last_dt).total_seconds() / 86400.0
        decay = math.pow(0.5, delta_days / self.half_life_days)
        return current_weight * decay

    def record_co_occurrence(self, memory_ids: List[str], context: str = ""):
        """
        Record all pairwise co-occurrences among the given memory IDs.
        For N ids, this records C(N,2) edges. Existing edges have their weight incremented by 1.
        """
        if len(memory_ids) < 2:
            return
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            for id_a, id_b in combinations(memory_ids, 2):
                a, b = self._canonical_pair(id_a, id_b)
                existing = conn.execute(
                    "SELECT weight FROM co_occurrence WHERE memory_a=? AND memory_b=?",
                    (a, b)
                ).fetchone()
                if existing:
                    new_weight = existing[0] + 1.0
                    conn.execute(
                        "UPDATE co_occurrence SET weight=?, last_updated=? WHERE memory_a=? AND memory_b=?",
                        (new_weight, now, a, b)
                    )
                else:
                    conn.execute(
                        "INSERT INTO co_occurrence (memory_a, memory_b, weight, last_updated, created_at) VALUES (?,?,?,?,?)",
                        (a, b, 1.0, now, now)
                    )
            conn.commit()

    def get_co_occurrence_score(self, memory_id: str, related_ids: List[str] = None) -> float:
        """
        Get the total co-occurrence weight for a memory_id.
        If related_ids is provided, sum weights only for those specific pairs.
        """
        with sqlite3.connect(self.db_path) as conn:
            if related_ids:
                total = 0.0
                for rid in related_ids:
                    a, b = self._canonical_pair(memory_id, rid)
                    row = conn.execute(
                        "SELECT weight, last_updated FROM co_occurrence WHERE memory_a=? AND memory_b=?",
                        (a, b)
                    ).fetchone()
                    if row:
                        total += self._compute_decay_weight(row[0], row[1])
                return total
            else:
                rows = conn.execute(
                    "SELECT weight, last_updated FROM co_occurrence WHERE memory_a=? OR memory_b=?",
                    (memory_id, memory_id)
                ).fetchall()
                return sum(self._compute_decay_weight(r[0], r[1]) for r in rows)

    def get_related_memories(self, memory_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Return the top_k most associated memories for a given memory_id.
        Results are sorted by effective weight (after decay) descending.
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT memory_a, memory_b, weight, last_updated FROM co_occurrence WHERE memory_a=? OR memory_b=?",
                (memory_id, memory_id)
            ).fetchall()

        results = []
        for row in rows:
            mem_a, mem_b, weight, last_updated = row
            partner = mem_b if mem_a == memory_id else mem_a
            effective_weight = self._compute_decay_weight(weight, last_updated)
            results.append((partner, effective_weight))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def get_stats(self) -> Dict:
        """Return statistics about the co-occurrence graph."""
        with sqlite3.connect(self.db_path) as conn:
            total_edges = conn.execute("SELECT COUNT(*) FROM co_occurrence").fetchone()[0]
            if total_edges == 0:
                return {
                    "total_edges": 0,
                    "unique_memories": 0,
                    "avg_weight": 0.0,
                    "max_weight": 0.0,
                    "min_weight": 0.0
                }
            avg_weight = conn.execute("SELECT AVG(weight) FROM co_occurrence").fetchone()[0]
            max_weight = conn.execute("SELECT MAX(weight) FROM co_occurrence").fetchone()[0]
            min_weight = conn.execute("SELECT MIN(weight) FROM co_occurrence").fetchone()[0]
            # Count unique memories
            ids_a = set(r[0] for r in conn.execute("SELECT DISTINCT memory_a FROM co_occurrence").fetchall())
            ids_b = set(r[0] for r in conn.execute("SELECT DISTINCT memory_b FROM co_occurrence").fetchall())
            unique_memories = len(ids_a | ids_b)

        return {
            "total_edges": total_edges,
            "unique_memories": unique_memories,
            "avg_weight": round(avg_weight, 4),
            "max_weight": round(max_weight, 4),
            "min_weight": round(min_weight, 4)
        }

    def decay_old_edges(self, days: int = 90) -> int:
        """
        Remove edges that haven't been updated in more than `days` days.
        Returns the number of deleted edges.
        """
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM co_occurrence WHERE last_updated < ?",
                (cutoff,)
            )
            conn.commit()
            return cursor.rowcount
'''

(workspace / "scripts" / "co_occurrence_tracker.py").write_text(co_occurrence_tracker_code)

# --- Create distractor files ---
(workspace / "scripts" / "__init__.py").write_text("")
(workspace / "scripts" / "memory_sync.py").write_text("# Legacy memory sync module\n# Deprecated\n")
(workspace / "scripts" / "embedding_utils.py").write_text("# Utility functions for embeddings\nimport numpy as np\n")
(workspace / "config" / "settings.yaml").write_text(
    "database:\n  host: localhost\n  port: 5432\n  name: researchdb\n\nlogging:\n  level: INFO\n"
)
(workspace / "config" / "legacy_graph.json").write_text(
    json.dumps({"version": "0.0.1", "deprecated": True, "nodes": [], "edges": []}, indent=2)
)
(workspace / "docs" / "architecture.md").write_text(
    "# Architecture\nThis system uses a star-topology memory architecture.\nSee plugin documentation for details.\n"
)
(workspace / "notebooks" / "exploration.py").write_text(
    "# Research exploration notebook\n# import pandas as pd\n# df = pd.read_csv('../data/raw_logs/session_001.csv')\n"
)
(workspace / "tests" / "test_dummy.py").write_text(
    "def test_placeholder():\n    assert True\n"
)
(workspace / "logs" / "app.log").write_text(
    "2024-01-15 10:00:00 INFO Starting service\n2024-01-15 10:00:01 INFO Connected to database\n"
)
(workspace / "data" / "archive" / "old_cooccurrence_dump.sql").write_text(
    "-- Legacy SQL dump, do not use\n-- INSERT INTO co_occurrence VALUES ('mem_old_1','mem_old_2',0.5,'2020-01-01','2020-01-01');\n"
)

# --- Generate the MAIN INPUT: raw co-retrieval session logs ---
# These represent biomedical research paper retrieval sessions.
# Each row is a comma-separated list of paper IDs retrieved together in one session.
# Some sessions are recent, some are old (for decay testing).

paper_ids = [f"paper_{i:03d}" for i in range(1, 31)]  # paper_001 to paper_030

# We want "paper_001" to be strongly associated with "paper_002" and "paper_003"
# "paper_010" should be associated with "paper_020" many times
# Some old sessions (over 100 days ago) to be decayed

sessions = []

# Strong cluster: paper_001, paper_002, paper_003 — 15 recent co-retrievals
for _ in range(15):
    sessions.append({
        "session_id": f"sess_{random.randint(10000,99999)}",
        "timestamp": (datetime.utcnow() - timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d"),
        "papers": "paper_001,paper_002,paper_003"
    })

# Another cluster: paper_010, paper_020 — 8 recent co-retrievals
for _ in range(8):
    sessions.append({
        "session_id": f"sess_{random.randint(10000,99999)}",
        "timestamp": (datetime.utcnow() - timedelta(days=random.randint(2, 7))).strftime("%Y-%m-%d"),
        "papers": "paper_010,paper_020"
    })

# paper_001 also co-retrieved with paper_005 — 5 times
for _ in range(5):
    sessions.append({
        "session_id": f"sess_{random.randint(10000,99999)}",
        "timestamp": (datetime.utcnow() - timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d"),
        "papers": "paper_001,paper_005"
    })

# paper_001 with paper_007 — 3 times
for _ in range(3):
    sessions.append({
        "session_id": f"sess_{random.randint(10000,99999)}",
        "timestamp": (datetime.utcnow() - timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d"),
        "papers": "paper_001,paper_007"
    })

# paper_001 with paper_009 — 2 times
for _ in range(2):
    sessions.append({
        "session_id": f"sess_{random.randint(10000,99999)}",
        "timestamp": (datetime.utcnow() - timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d"),
        "papers": "paper_001,paper_009"
    })

# OLD sessions (120+ days ago) — should be pruned by decay_old_edges(days=90)
old_pairs = [
    ("paper_015", "paper_016"),
    ("paper_017", "paper_018"),
    ("paper_019", "paper_025"),
    ("paper_022", "paper_023"),
    ("paper_024", "paper_026"),
]
for pair in old_pairs:
    for _ in range(random.randint(2, 4)):
        sessions.append({
            "session_id": f"sess_{random.randint(10000,99999)}",
            "timestamp": (datetime.utcnow() - timedelta(days=random.randint(120, 200))).strftime("%Y-%m-%d"),
            "papers": f"{pair[0]},{pair[1]}"
        })

# Some random noise sessions
for _ in range(10):
    chosen = random.sample(paper_ids[10:25], k=2)
    sessions.append({
        "session_id": f"sess_{random.randint(10000,99999)}",
        "timestamp": (datetime.utcnow() - timedelta(days=random.randint(50, 80))).strftime("%Y-%m-%d"),
        "papers": ",".join(chosen)
    })

random.shuffle(sessions)

# Write sessions CSV
sessions_csv_path = workspace / "data" / "raw_logs" / "retrieval_sessions.csv"
with open(sessions_csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["session_id", "timestamp", "papers"])
    writer.writeheader()
    for s in sessions:
        writer.writerow(s)

# Write a smaller "priority sessions" file — these are 3-paper sessions that should generate 3 edges each
priority_sessions = [
    {"session_id": "sess_PRIO_001", "timestamp": datetime.utcnow().strftime("%Y-%m-%d"), "papers": "paper_001,paper_002,paper_003"},
    {"session_id": "sess_PRIO_002", "timestamp": datetime.utcnow().strftime("%Y-%m-%d"), "papers": "paper_010,paper_020,paper_015"},
]
priority_path = workspace / "data" / "raw_logs" / "priority_sessions.csv"
with open(priority_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["session_id", "timestamp", "papers"])
    writer.writeheader()
    for s in priority_sessions:
        writer.writerow(s)

# Write task specification (what the agent needs to produce)
task_spec = {
    "task": "Build and analyze the paper association graph",
    "input_files": [
        "data/raw_logs/retrieval_sessions.csv",
        "data/raw_logs/priority_sessions.csv"
    ],
    "steps": [
        "Load ALL sessions from both CSV files into the association engine",
        "Remove stale associations (older than 90 days)",
        "Query top-5 papers most associated with paper_001",
        "Save final statistics and query results to reports/association_report.json"
    ],
    "output_file": "reports/association_report.json"
}
(workspace / "data" / "processed" / "task_spec.json").write_text(json.dumps(task_spec, indent=2))

print("Workspace initialized successfully.")
print(f"Sessions file: {sessions_csv_path} ({len(sessions)} rows)")
print(f"Priority sessions: {priority_path}")