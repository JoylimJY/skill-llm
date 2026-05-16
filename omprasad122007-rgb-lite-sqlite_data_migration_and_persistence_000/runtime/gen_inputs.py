import os
import json
import random
import datetime

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure (distractor files) ---
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/exports",
    "config",
    "logs/2024",
    "logs/2025",
    "backups",
    "agents/alpha",
    "agents/beta",
    "agents/gamma",
    "reports",
    "migrations",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "config/agent_config.yaml": "fleet_name: OpenClaw-Edge\nmax_agents: 12\nlog_level: INFO\nttl_hours: 24\n",
    "config/db_settings.ini": "[database]\nmode=file\npath=agent_storage.db\ncache_mb=64\n",
    "data/exports/schema_dump.txt": "-- Legacy schema dump\nCREATE TABLE old_memos (id INTEGER, note TEXT);\n",
    "logs/2024/error.log": "2024-11-01 WARN agent_alpha: cache miss\n2024-11-02 ERROR agent_beta: timeout\n",
    "logs/2025/error.log": "2025-01-15 WARN agent_gamma: stale entry\n",
    "reports/weekly_summary.txt": "Agents processed 12,400 events this week.\nCache hit rate: 67%\n",
    "migrations/v1_notes.txt": "Migration from flat JSON to structured DB.\nExpiry column must be ISO8601 format.\n",
    "migrations/v2_notes.txt": "Add 'severity' column to session_logs for triage.\n",
    "agents/alpha/status.txt": "agent_id: alpha-001\nstatus: active\nlast_seen: 2025-06-01T10:00:00\n",
    "agents/beta/status.txt": "agent_id: beta-007\nstatus: idle\nlast_seen: 2025-06-01T09:45:00\n",
    "agents/gamma/status.txt": "agent_id: gamma-013\nstatus: degraded\nlast_seen: 2025-05-30T22:10:00\n",
    "data/processed/.gitkeep": "",
}
for path, content in distractors.items():
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# --- sqlite_connector.py (the bespoke wrapper the agent must use) ---
sqlite_connector_code = '''
import sqlite3
import os
import json
import shutil
from datetime import datetime

class SQLiteDB:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        # auto-wal mode enabled
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA temp_store=MEMORY")
        self.conn.commit()

    def create_table(self, table, schema_dict):
        cols = ", ".join(f"{col} {typ}" for col, typ in schema_dict.items())
        self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols})")
        self.conn.commit()

    def create_index(self, table, columns):
        index_name = f"idx_{table}_{columns.replace(', ', '_').replace(',', '_')}"
        self.conn.execute(
            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({columns})"
        )
        self.conn.commit()

    def insert(self, table, data):
        if isinstance(data, dict):
            cols = ", ".join(data.keys())
            placeholders = ", ".join("?" * len(data))
            self.conn.execute(
                f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
                list(data.values())
            )
            self.conn.commit()
        else:
            raise ValueError("insert() requires a dict")

    def insert_or_replace(self, table, data):
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        self.conn.execute(
            f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})",
            list(data.values())
        )
        self.conn.commit()

    def batch_insert(self, table, rows):
        if not rows:
            return
        cols = ", ".join(rows[0].keys())
        placeholders = ", ".join("?" * len(rows[0]))
        self.conn.executemany(
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
            [list(r.values()) for r in rows]
        )
        self.conn.commit()

    def query(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def query_one(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

    def update(self, table, condition, data, params=()):
        if isinstance(data, dict):
            set_clause = ", ".join(f"{k} = ?" for k in data.keys())
            values = list(data.values()) + list(params)
            self.conn.execute(
                f"UPDATE {table} SET {set_clause} WHERE {condition}",
                values
            )
            self.conn.commit()
        else:
            raise ValueError("update() requires a dict for data")

    def delete(self, table, condition, params=()):
        self.conn.execute(f"DELETE FROM {table} WHERE {condition}", params)
        self.conn.commit()

    def add_column(self, table, column, column_type):
        try:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

    def migrate(self, table, column_mapping):
        for old_col, new_col in column_mapping.items():
            self.conn.execute(f"UPDATE {table} SET {new_col} = {old_col}")
            self.conn.commit()

    def backup(self, dest_path):
        dest_conn = sqlite3.connect(dest_path)
        self.conn.backup(dest_conn)
        dest_conn.close()

    def auto_backup(self, directory, interval):
        os.makedirs(directory, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(directory, f"backup_{interval}_{timestamp}.db")
        self.backup(dest)
        return dest

    def cleanup_expired(self, table, expires_col):
        now = datetime.now().isoformat()
        self.conn.execute(
            f"DELETE FROM {table} WHERE {expires_col} < ?", (now,)
        )
        self.conn.commit()

    def cleanup_old(self, table, date_col, days=7):
        cutoff = (datetime.now() - __import__("datetime").timedelta(days=days)).isoformat()
        self.conn.execute(
            f"DELETE FROM {table} WHERE {date_col} < ?", (cutoff,)
        )
        self.conn.commit()

    def vacuum(self):
        self.conn.execute("VACUUM")
        self.conn.commit()

    def close(self):
        self.conn.close()


class ConnectionPool:
    def __init__(self, path, max_connections=5, timeout=5.0):
        self.path = path
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool = []

    def get_connection(self):
        if self._pool:
            return self._pool.pop()
        conn = sqlite3.connect(self.path, timeout=self.timeout)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def release_connection(self, conn):
        if len(self._pool) < self.max_connections:
            self._pool.append(conn)
        else:
            conn.close()
'''
with open(os.path.join(WORKSPACE, "scripts/sqlite_connector.py"), "w") as f:
    f.write(sqlite_connector_code)

# Also place at top-level for convenience (the skill shows `from sqlite_connector import SQLiteDB`)
with open(os.path.join(WORKSPACE, "sqlite_connector.py"), "w") as f:
    f.write(sqlite_connector_code)

# --- CLI tool ---
cli_code = '''#!/usr/bin/env python3
import sys
import json
import argparse
import sqlite3

def main():
    parser = argparse.ArgumentParser(description="SQLite CLI for OpenClaw agents")
    sub = parser.add_subparsers(dest="cmd")

    p_create = sub.add_parser("create")
    p_create.add_argument("db_path")

    p_table = sub.add_parser("create-table")
    p_table.add_argument("table")
    p_table.add_argument("-c", "--col", action="append", dest="cols")
    p_table.add_argument("--db", default="agent_data.db")

    p_insert = sub.add_parser("insert")
    p_insert.add_argument("table")
    p_insert.add_argument("data")
    p_insert.add_argument("--db", default="agent_data.db")

    p_query = sub.add_parser("query")
    p_query.add_argument("sql")
    p_query.add_argument("--db", default="agent_data.db")

    p_opt = sub.add_parser("optimize")
    p_opt.add_argument("db_path")

    args = parser.parse_args()

    if args.cmd == "create":
        conn = sqlite3.connect(args.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.close()
        print(f"Created {args.db_path}")

    elif args.cmd == "optimize":
        conn = sqlite3.connect(args.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("VACUUM")
        conn.close()
        print(f"Optimized {args.db_path}")

    elif args.cmd == "query":
        conn = sqlite3.connect(args.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(args.sql).fetchall()
        for row in rows:
            print(json.dumps(dict(row)))
        conn.close()

    elif args.cmd == "insert":
        data = json.loads(args.data)
        conn = sqlite3.connect(args.db_path)
        cols = ", ".join(data.keys())
        ph = ", ".join("?" * len(data))
        conn.execute(f"INSERT INTO {args.table} ({cols}) VALUES ({ph})", list(data.values()))
        conn.commit()
        conn.close()
        print("Inserted.")

if __name__ == "__main__":
    main()
'''
with open(os.path.join(WORKSPACE, "scripts/sqlite_cli.py"), "w") as f:
    f.write(cli_code)
os.chmod(os.path.join(WORKSPACE, "scripts/sqlite_cli.py"), 0o755)

# --- Raw messy input data: JSON session logs to migrate ---
now = datetime.datetime.now()

session_logs_raw = []
agents = ["alpha-001", "beta-007", "gamma-013"]
messages = [
    "sensor_reading OK",
    "heartbeat sent",
    "cache flush triggered",
    "anomaly detected: voltage spike",
    "config reload",
    "emergency shutdown sequence",
    "reconnected to mesh",
    "memory threshold exceeded",
]
for i in range(30):
    ts = (now - datetime.timedelta(hours=random.randint(1, 200))).isoformat()
    session_logs_raw.append({
        "session_id": f"sess-{random.randint(1000,9999)}",
        "agent": random.choice(agents),
        "message": random.choice(messages),
        "metadata": json.dumps({"event_index": i, "severity": random.choice(["low", "medium", "high"])}),
        "created_at": ts,
    })

with open(os.path.join(WORKSPACE, "data/raw/session_logs.json"), "w") as f:
    json.dump(session_logs_raw, f, indent=2)

# --- Raw memo data to ingest ---
memo_data_raw = []
for i in range(20):
    ago_hours = random.randint(1, 48)
    expires_hours = random.randint(-5, 30)  # some already expired, some future
    created = (now - datetime.timedelta(hours=ago_hours)).isoformat()
    expires = (now + datetime.timedelta(hours=expires_hours)).isoformat()
    memo_data_raw.append({
        "agent_id": random.choice(agents),
        "key": f"memo_key_{i:03d}",
        "value": json.dumps({"data": f"payload_{i}", "checksum": random.randint(1000, 9999)}),
        "priority": random.randint(0, 5),
        "created_at": created,
        "expires_at": expires,
    })

with open(os.path.join(WORKSPACE, "data/raw/agent_memos.json"), "w") as f:
    json.dump(memo_data_raw, f, indent=2)

# --- Raw cache entries (some expired, some valid) ---
cache_entries_raw = []
cache_keys = [f"edge_sensor_{chr(65+i)}" for i in range(12)]
for i, key in enumerate(cache_keys):
    # Alternate expired/valid
    if i % 3 == 0:
        expires = (now - datetime.timedelta(hours=random.randint(1, 10))).isoformat()  # expired
    else:
        expires = (now + datetime.timedelta(hours=random.randint(1, 48))).isoformat()  # valid
    cache_entries_raw.append({
        "key": key,
        "value": json.dumps({"reading": round(random.uniform(0, 100), 2), "unit": "mV"}),
        "created_at": now.isoformat(),
        "expires_at": expires,
    })

with open(os.path.join(WORKSPACE, "data/raw/cache_entries.json"), "w") as f:
    json.dump(cache_entries_raw, f, indent=2)

print("Workspace generated successfully.")
print(f"  - {len(session_logs_raw)} session log entries")
print(f"  - {len(memo_data_raw)} agent memo entries ({sum(1 for m in memo_data_raw if m['expires_at'] < now.isoformat())} already expired)")
print(f"  - {len(cache_entries_raw)} cache entries ({sum(1 for c in cache_entries_raw if c['expires_at'] < now.isoformat())} already expired)")