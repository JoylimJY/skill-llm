import os
import random
import json
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Skill workspace layout ────────────────────────────────────────────────────
skill_dir = workspace / "skills" / "tidbyt-status"
scripts_dir = skill_dir / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = [
    workspace / "config" / "app.yaml",
    workspace / "config" / "network.json",
    workspace / "logs" / "system.log",
    workspace / "logs" / "errors.log",
    workspace / "data" / "metrics" / "cpu.csv",
    workspace / "data" / "metrics" / "memory.csv",
    workspace / "data" / "sessions" / "old_session.jsonl",   # RED HERRING: wrong path
    workspace / "agents" / "config.json",
    workspace / "agents" / "manifest.yaml",
    workspace / "tmp" / "cache" / "render.webp",
    workspace / "tmp" / "cache" / "preview.png",
    workspace / "docs" / "architecture.md",
]

for d in distractors:
    d.parent.mkdir(parents=True, exist_ok=True)
    d.write_text(f"# distractor file: {d.name}\ngenerated_by: gen_inputs\n")

# ── Misleading config in wrong location (trap) ───────────────────────────────
wrong_sessions = workspace / "data" / "sessions"
wrong_sessions.mkdir(parents=True, exist_ok=True)
for i in range(3):
    f = wrong_sessions / f"session_{i}.jsonl"
    f.write_text(json.dumps({"role": "user", "content": f"test message {i}"}) + "\n")

# ── Stale openclaw session dir with OLD files (should trigger sleeping) ───────
# The REAL sessions dir is ~/.openclaw/agents/main/sessions/ — the agent must discover this
openclaw_stale = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
openclaw_stale.mkdir(parents=True, exist_ok=True)

# Write a stale main session (old mtime → sleeping if agent doesn't set up fresh files)
stale_main = openclaw_stale / "main.jsonl"
stale_main.write_text(json.dumps({"role": "assistant", "content": "old conversation"}) + "\n")
# Age this file by 2 hours (7200 seconds)
import time
old_time = time.time() - 7200
os.utime(stale_main, (old_time, old_time))

# ── The canonical status_server.py (pre-existing per SKILL.md) ───────────────
status_server_code = r'''#!/usr/bin/env python3
"""Scout Status API Server for Tidbyt LED display integration."""

import json
import os
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

AGENT_NAME = "Scout"
AGENT_EMOJI = "\U0001f985"  # 🦅
SESSIONS_DIR = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
ACTIVITY_THRESHOLD = 300  # seconds — default 300 (5 minutes)
PORT = int(os.environ.get("PORT", 8765))


def get_agent_status():
    """Detect agent status from session files."""
    sessions_dir = SESSIONS_DIR

    if not sessions_dir.exists():
        return {
            "agent": AGENT_NAME,
            "emoji": AGENT_EMOJI,
            "status": "sleeping",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "active_tasks": 0,
            "last_activity": None,
            "recent_activity": "No session directory found",
        }

    now = time.time()
    all_sessions = list(sessions_dir.glob("*.jsonl"))

    active_sessions = []
    newest_mtime = None

    for session_file in all_sessions:
        try:
            mtime = session_file.stat().st_mtime
            age = now - mtime
            if newest_mtime is None or mtime > newest_mtime:
                newest_mtime = mtime
            if age < ACTIVITY_THRESHOLD:
                active_sessions.append(session_file)
        except OSError:
            continue

    # Sub-agent tasks: active sessions that are NOT the main session
    sub_agent_tasks = [
        s for s in active_sessions if "main" not in s.stem.lower()
    ]
    active_tasks = len(sub_agent_tasks)

    if newest_mtime:
        last_activity_dt = datetime.fromtimestamp(newest_mtime)
        last_activity_str = last_activity_dt.isoformat(timespec="seconds")
        age_of_newest = now - newest_mtime
    else:
        last_activity_str = None
        age_of_newest = float("inf")

    # Determine status
    if not active_sessions:
        status = "sleeping"
        recent_activity = (
            f"Last active {int(age_of_newest // 60)} minutes ago"
            if newest_mtime
            else "No recent activity"
        )
    elif active_tasks > 0:
        status = "working"
        recent_activity = f"Running {active_tasks} background task(s)"
    else:
        # Main session active, no sub-agents
        status = "chatting"
        recent_activity = "Chatting with user..."

    return {
        "agent": AGENT_NAME,
        "emoji": AGENT_EMOJI,
        "status": status,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "active_tasks": active_tasks,
        "last_activity": last_activity_str,
        "recent_activity": recent_activity,
    }


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            payload = get_agent_status()
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass  # suppress request logs


def run():
    server = HTTPServer(("0.0.0.0", PORT), StatusHandler)
    print(f"Scout Status API running on port {PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    run()
'''

server_file = scripts_dir / "status_server.py"
server_file.write_text(status_server_code)
server_file.chmod(server_file.stat().st_mode | stat.S_IEXEC)

# ── SKILL.md inside the skill directory ──────────────────────────────────────
skill_md = skill_dir / "SKILL.md"
skill_md.write_text("""# tidbyt-status skill — see project root SKILL.md for full documentation.\n""")

# ── scout_status.star placeholder ────────────────────────────────────────────
star_file = skill_dir / "scout_status.star"
star_file.write_text('''DEFAULT_API_URL = "http://YOUR-LOCAL-IP:8765/status"\n''')

# ── Stray JSON file that looks like an API response (RED HERRING) ─────────────
fake_snapshot = workspace / "tmp" / "cache" / "status_old.json"
fake_snapshot.write_text(json.dumps({
    "agent": "Scout",
    "emoji": "🦅",
    "status": "sleeping",
    "timestamp": "2024-01-01T00:00:00",
    "active_tasks": 0,
    "last_activity": None,
    "recent_activity": "Outdated snapshot — do not use"
}, ensure_ascii=False, indent=2))

print("Workspace generated successfully.")
print(f"Skill dir: {skill_dir}")
print(f"Status server: {server_file}")
print(f"Stale sessions at: {openclaw_stale}")