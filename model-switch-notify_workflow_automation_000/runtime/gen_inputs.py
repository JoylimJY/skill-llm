import os
import json
import sqlite3
import random
import shutil
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Create the openclaw skill directory structure ──────────────────────────────
skill_dir = Path.home() / ".openclaw" / "skills" / "model-switch-notify" / "scripts"
skill_dir.mkdir(parents=True, exist_ok=True)
data_dir = Path.home() / ".openclaw" / "data"
data_dir.mkdir(parents=True, exist_ok=True)

# ── Write the actual check_model.py script ────────────────────────────────────
check_model_script = skill_dir / "check_model.py"
check_model_script.write_text(r'''#!/usr/bin/env python3
"""
Model Switch Notify - check_model.py
Manages model state and switch notifications using SQLite.
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".openclaw" / "data" / "model-switch.db"

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS model_states (
            agent_id TEXT PRIMARY KEY,
            last_model TEXT NOT NULL,
            last_notify TIMESTAMP,
            last_heartbeat TIMESTAMP,
            channel TEXT,
            session TEXT,
            pending_notify INTEGER DEFAULT 0,
            pending_message TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def cmd_check(args):
    conn = get_db()
    now = datetime.utcnow().isoformat()

    row = conn.execute(
        "SELECT * FROM model_states WHERE agent_id = ?", (args.agent,)
    ).fetchone()

    result = {
        "changed": False,
        "previousModel": None,
        "currentModel": args.current_model,
        "shouldNotify": False,
        "notifyMessage": None,
        "firstTime": False,
        "pendingNotify": False,
        "pendingMessage": None,
    }

    if row is None:
        # First time
        result["firstTime"] = True
        result["shouldNotify"] = True
        result["notifyMessage"] = f"当前使用模型：{args.current_model}"
        conn.execute(
            """INSERT INTO model_states
               (agent_id, last_model, last_notify, last_heartbeat, channel, session,
                pending_notify, pending_message, updated_at)
               VALUES (?,?,?,?,?,?,0,NULL,?)""",
            (args.agent, args.current_model, now, now,
             getattr(args, "channel", None), getattr(args, "session", None), now)
        )
        conn.commit()
        print(json.dumps(result, ensure_ascii=False))
        return

    prev_model = row["last_model"]
    pending = row["pending_notify"]
    pending_msg = row["pending_message"]

    # Check pending first
    if pending:
        result["pendingNotify"] = True
        result["pendingMessage"] = pending_msg
        result["shouldNotify"] = True
        # Clear pending
        conn.execute(
            "UPDATE model_states SET pending_notify=0, pending_message=NULL WHERE agent_id=?",
            (args.agent,)
        )

    # Check model change
    if prev_model != args.current_model:
        result["changed"] = True
        result["previousModel"] = prev_model
        result["shouldNotify"] = True
        result["notifyMessage"] = f"老板，模型已切换，当前使用：{args.current_model}"
        conn.execute(
            """UPDATE model_states SET last_model=?, last_notify=?, last_heartbeat=?,
               channel=?, session=?, updated_at=? WHERE agent_id=?""",
            (args.current_model, now, now,
             getattr(args, "channel", None), getattr(args, "session", None),
             now, args.agent)
        )
    else:
        conn.execute(
            "UPDATE model_states SET last_heartbeat=?, updated_at=? WHERE agent_id=?",
            (now, now, args.agent)
        )

    conn.commit()
    print(json.dumps(result, ensure_ascii=False))

def cmd_heartbeat(args):
    conn = get_db()
    now = datetime.utcnow().isoformat()
    row = conn.execute(
        "SELECT * FROM model_states WHERE agent_id=?", (args.agent,)
    ).fetchone()
    if row is None:
        conn.execute(
            """INSERT INTO model_states
               (agent_id, last_model, last_heartbeat, updated_at)
               VALUES (?,?,?,?)""",
            (args.agent, args.current_model, now, now)
        )
    else:
        conn.execute(
            """UPDATE model_states SET last_model=?, last_heartbeat=?, updated_at=?
               WHERE agent_id=?""",
            (args.current_model, now, now, args.agent)
        )
    conn.commit()
    print(json.dumps({"status": "ok", "agent": args.agent,
                      "model": args.current_model, "heartbeat": now},
                     ensure_ascii=False))

def cmd_interrupt(args):
    conn = get_db()
    now = datetime.utcnow().isoformat()
    row = conn.execute(
        "SELECT * FROM model_states WHERE agent_id=?", (args.agent,)
    ).fetchone()
    msg = args.message if args.message else f"[上次未发送] 老板，模型已切换，当前使用：{args.model}"
    if row is None:
        conn.execute(
            """INSERT INTO model_states
               (agent_id, last_model, pending_notify, pending_message, updated_at)
               VALUES (?,?,1,?,?)""",
            (args.agent, args.model, msg, now)
        )
    else:
        conn.execute(
            """UPDATE model_states SET last_model=?, pending_notify=1,
               pending_message=?, updated_at=? WHERE agent_id=?""",
            (args.model, msg, now, args.agent)
        )
    conn.commit()
    print(json.dumps({"status": "ok", "agent": args.agent,
                      "pendingMessage": msg}, ensure_ascii=False))

def cmd_get(args):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM model_states WHERE agent_id=?", (args.agent,)
    ).fetchone()
    if row is None:
        print(json.dumps({"error": "not found"}, ensure_ascii=False))
        return
    print(json.dumps(dict(row), ensure_ascii=False))

def cmd_list(args):
    conn = get_db()
    rows = conn.execute("SELECT * FROM model_states").fetchall()
    print(json.dumps([dict(r) for r in rows], ensure_ascii=False))

def cmd_reset(args):
    conn = get_db()
    conn.execute("DELETE FROM model_states WHERE agent_id=?", (args.agent,))
    conn.commit()
    print(json.dumps({"status": "ok", "agent": args.agent}, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    p_check = sub.add_parser("check")
    p_check.add_argument("--agent", required=True)
    p_check.add_argument("--current-model", required=True)
    p_check.add_argument("--channel")
    p_check.add_argument("--session")

    p_hb = sub.add_parser("heartbeat")
    p_hb.add_argument("--agent", required=True)
    p_hb.add_argument("--current-model", required=True)

    p_int = sub.add_parser("interrupt")
    p_int.add_argument("--agent", required=True)
    p_int.add_argument("--model", required=True)
    p_int.add_argument("--message")

    p_get = sub.add_parser("get")
    p_get.add_argument("--agent", required=True)

    p_list = sub.add_parser("list")

    p_reset = sub.add_parser("reset")
    p_reset.add_argument("--agent", required=True)

    args = parser.parse_args()

    dispatch = {
        "check": cmd_check,
        "heartbeat": cmd_heartbeat,
        "interrupt": cmd_interrupt,
        "get": cmd_get,
        "list": cmd_list,
        "reset": cmd_reset,
    }
    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
''')
check_model_script.chmod(0o755)

# ── Also make it accessible as check_model.py directly in /workspace ─────────
shutil.copy(str(check_model_script), str(workspace / "check_model.py"))

# ── Pre-populate DB with existing agents to make environment realistic ─────────
db_path = data_dir / "model-switch.db"
conn = sqlite3.connect(str(db_path))
conn.execute("""
    CREATE TABLE IF NOT EXISTS model_states (
        agent_id TEXT PRIMARY KEY,
        last_model TEXT NOT NULL,
        last_notify TIMESTAMP,
        last_heartbeat TIMESTAMP,
        channel TEXT,
        session TEXT,
        pending_notify INTEGER DEFAULT 0,
        pending_message TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

past_time = (datetime.utcnow() - timedelta(hours=3)).isoformat()
past_time2 = (datetime.utcnow() - timedelta(hours=1)).isoformat()

# "writer" agent - stable, no pending, no change expected
conn.execute("""
    INSERT OR REPLACE INTO model_states
    (agent_id, last_model, last_notify, last_heartbeat, channel, session,
     pending_notify, pending_message, updated_at)
    VALUES (?,?,?,?,?,?,0,NULL,?)
""", ("writer", "ollama/glm-4:cloud", past_time, past_time2,
      "slack", "slack:channel:general", past_time2))

# "analyst" agent - has NO pending (clean state, last model = deepseek)
conn.execute("""
    INSERT OR REPLACE INTO model_states
    (agent_id, last_model, last_notify, last_heartbeat, channel, session,
     pending_notify, pending_message, updated_at)
    VALUES (?,?,?,?,?,?,0,NULL,?)
""", ("analyst", "ollama/deepseek-r1:7b", past_time, past_time,
      "qqbot", "qqbot:c2c:analyst01", past_time))

conn.commit()
conn.close()

# ── Create distractor files in workspace ──────────────────────────────────────
(workspace / "ops_logs").mkdir(exist_ok=True)
(workspace / "ops_logs" / "agent_activity_2024-01.log").write_text(
    "2024-01-15 10:22:01 [coder] session started model=ollama/glm-5:cloud\n"
    "2024-01-15 10:22:45 [coder] response sent\n"
    "2024-01-15 11:05:12 [analyst] session started model=ollama/deepseek-r1:7b\n"
)
(workspace / "ops_logs" / "agent_activity_2024-02.log").write_text(
    "2024-02-01 09:00:00 [writer] model change detected glm-4:cloud -> qwen3:14b\n"
    "2024-02-01 09:00:01 [writer] notification sent\n"
)
(workspace / "ops_logs" / "errors.log").write_text(
    "2024-02-10 15:32:00 ERROR connection timeout session=qqbot:c2c:analyst01\n"
    "2024-02-10 15:32:01 ERROR notification delivery failed agent=analyst\n"
    "2024-02-10 15:32:02 INFO retry scheduled\n"
)

(workspace / "config").mkdir(exist_ok=True)
(workspace / "config" / "agents.yaml").write_text(
    "agents:\n"
    "  - id: coder\n"
    "    channel: qqbot\n"
    "    default_model: ollama/qwen3.5-code\n"
    "  - id: analyst\n"
    "    channel: qqbot\n"
    "    default_model: ollama/deepseek-r1:7b\n"
    "  - id: writer\n"
    "    channel: slack\n"
    "    default_model: ollama/glm-4:cloud\n"
)
(workspace / "config" / "channels.json").write_text(json.dumps({
    "qqbot": {"type": "qq", "group": "c2c"},
    "slack": {"type": "slack", "workspace": "openclaw"},
}, indent=2))
(workspace / "config" / "legacy_model_map.json").write_text(json.dumps({
    "glm-5:cloud": "ollama/glm-5:cloud",
    "qwen3.5-code": "ollama/qwen3.5-code",
    "deepseek-r1": "ollama/deepseek-r1:7b",
}, indent=2))

(workspace / "scripts").mkdir(exist_ok=True)
(workspace / "scripts" / "deploy_agent.sh").write_text(
    "#!/bin/bash\n# Deploy agent to production\necho 'Deploying agent: $1'\n"
)
(workspace / "scripts" / "rotate_keys.sh").write_text(
    "#!/bin/bash\n# Rotate API keys\necho 'Key rotation: not implemented'\n"
)
(workspace / "scripts" / "health_check.sh").write_text(
    "#!/bin/bash\ncurl -s http://localhost:8080/health\n"
)

(workspace / "reports").mkdir(exist_ok=True)
(workspace / "reports" / "model_usage_jan.csv").write_text(
    "date,agent,model,sessions\n"
    "2024-01-01,coder,ollama/glm-5:cloud,42\n"
    "2024-01-02,coder,ollama/glm-5:cloud,38\n"
    "2024-01-15,analyst,ollama/deepseek-r1:7b,15\n"
)
(workspace / "reports" / "notification_failures.txt").write_text(
    "2024-02-10: analyst - delivery failed (timeout)\n"
    "2024-02-11: coder - delivery failed (disconnect)\n"
)

(workspace / "archive").mkdir(exist_ok=True)
(workspace / "archive" / "old_model_states.json").write_text(json.dumps({
    "coder": {"last_model": "ollama/glm-5:cloud", "updated": "2024-01-10"},
    "analyst": {"last_model": "ollama/llama2:13b", "updated": "2024-01-05"},
}, indent=2))
(workspace / "archive" / "v2_migration_notes.txt").write_text(
    "v2->v3 migration: JSON storage deprecated. Use SQLite only.\n"
    "DB path: ~/.openclaw/data/model-switch.db\n"
    "Old JSON files in archive/ are no longer active.\n"
)

print("Workspace initialized successfully.")
print(f"DB created at: {db_path}")
print(f"check_model.py available at: {check_model_script} and {workspace}/check_model.py")