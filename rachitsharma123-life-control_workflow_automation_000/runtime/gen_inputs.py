#!/usr/bin/env python3
"""
Generates the sandbox workspace for the Life Control skill evaluation task.
Creates the realistic directory structure, mock CLI tools, distractor files,
and a messy/incomplete initial state that the agent must fix.
"""
import os
import stat
import json
import textwrap
from pathlib import Path

WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

def make_dirs(*paths):
    for p in paths:
        (WORKSPACE / p).mkdir(parents=True, exist_ok=True)

def write_file(rel_path, content, executable=False):
    p = WORKSPACE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content))
    if executable:
        p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Directory skeleton ────────────────────────────────────────────────────────
make_dirs(
    "skills/life-control/scripts",
    "skills/life-control/routines",
    "skills/life-control/references",
    "skills/life-control/bin",
    "skills/life-control/db",
    "skills/life-control/logs",
    "skills/life-control/templates",
    "docs/archive",
    "docs/onboarding",
    "config/legacy",
    "config/env",
    "tests/unit",
    "tests/integration",
)

# ── SKILL.md ──────────────────────────────────────────────────────────────────
write_file("SKILL.md", """\
    ---
    name: life-control
    description: "Orchestrate the Life Control CLI skill for OpenClaw agent fleets: initialize the Life Control database, register agent personas, wire Telegram bots, and run daily routines (Morning Alignment, Body Protocol, Financial Pulse, Social Radar, Work Priming, Shutdown). Use when a user asks to create or run a Life Control system, OpenClaw skill integration, or agent persona automation for personal life tracking."
    ---

    # Life Control

    ## Overview
    Set up and operate the Life Control CLI so OpenClaw can run agent personas that track life domains (wellness, finance, fashion, career, relationships, spiritual growth) with routines and Telegram notifications.

    ## Quick start (OpenClaw)
    1. Ensure the repo root is available.
    2. Export Telegram chat ID + agent bot tokens.
    3. Run `skills/life-control/scripts/bootstrap.sh`.
    4. Use `lc dashboard`, `lc list`, and routine scripts to coordinate.

    If you need persona mappings or OpenClaw-specific notes, load `references/openclaw.md`.

    ## Core workflows

    ### 1) Bootstrap personas
    - Run `skills/life-control/scripts/bootstrap.sh`.
    - Verify agents with `lc fleet`.

    ### 2) Add goals + logs
    - Use `lc add` and `lc log` for structured tracking.
    - Use `qlog` for quick metrics (protein, water, workout, expense, meditate).

    ### 3) Run daily routines
    - Scripts live in `routines/` (Morning Alignment, Body Protocol, Financial Pulse, Social Radar, Work Priming, Shutdown).
    - Add `crontab-template.txt` entries for automatic scheduling.

    ### 4) Telegram notifications
    - Use `lc notify` to queue messages per agent.
    - Run `telegram-sender.sh` via cron to deliver to each bot.

    ## Resources

    ### scripts/
    - `bootstrap.sh`: initializes the DB and registers persona agents by calling `setup-agents.sh`.

    ### references/
    - `openclaw.md`: persona mapping + OpenClaw integration notes.
    """)

# ── references/openclaw.md ────────────────────────────────────────────────────
write_file("skills/life-control/references/openclaw.md", """\
    # OpenClaw Integration Notes

    ## Persona Mapping
    The Life Control system uses the following canonical agent personas.
    Each persona owns a specific life domain:

    | Persona    | Domain              | Agent ID    |
    |------------|---------------------|-------------|
    | Aurelius   | Wellness & Mindset  | oc-001      |
    | Cassian    | Finance & Career    | oc-002      |
    | Vesper     | Social & Fashion    | oc-003      |
    | Solenne    | Spiritual Growth    | oc-004      |

    ## Registration Rules
    - All four personas MUST be registered during bootstrap.
    - Each persona requires: name, domain, agent_id (exactly as above).
    - After bootstrap, `lc fleet` MUST list all four with status=active.

    ## Goal Conventions
    - Goals are tied to a persona by agent_id.
    - Goal titles must be plain English, max 80 chars.
    - Priority levels: low | medium | high | critical

    ## Quick-log (qlog) Conventions
    Accepted metric types (EXACT strings, lowercase):
      protein    – grams (integer)
      water      – ml (integer)
      workout    – minutes (integer)
      expense    – amount in cents (integer)
      meditate   – minutes (integer)

    Syntax:
      qlog <metric_type> <value> [--agent <agent_id>]

    Example:
      qlog protein 120 --agent oc-001
      qlog expense 4500 --agent oc-002

    ## Routine Scripts
    Each routine script in `routines/` must be run with its agent context:
      bash routines/<routine-name>.sh <agent_id>

    Routine output is appended to `logs/<agent_id>-<routine-name>.log`.

    ## Notification Queue
    `lc notify <agent_id> "<message>"` appends to the agent's notification queue.
    Queue file: `db/notify-queue-<agent_id>.txt`

    ## DB Path
    Default: `skills/life-control/db/life-control.db`
    Override via: `LC_DB_PATH` environment variable.
    """)

# ── The actual LC CLI tool ────────────────────────────────────────────────────
write_file("skills/life-control/bin/lc", """\
    #!/usr/bin/env python3
    \"\"\"Life Control CLI (lc) - mock implementation for OpenClaw skill sandbox.\"\"\"
    import sys, os, json, sqlite3, datetime, click
    from pathlib import Path

    DB_PATH = Path(os.environ.get("LC_DB_PATH",
                   str(Path(__file__).parent.parent / "db" / "life-control.db")))

    def get_conn():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(conn):
        conn.executescript(\"\"\"
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                domain TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                title TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(agent_id) REFERENCES agents(agent_id)
            );
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                value INTEGER NOT NULL,
                logged_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                message TEXT NOT NULL,
                queued_at TEXT DEFAULT (datetime('now')),
                sent INTEGER DEFAULT 0
            );
        \"\"\")
        conn.commit()

    @click.group()
    def cli():
        pass

    @cli.command()
    def dashboard():
        conn = get_conn(); init_db(conn)
        agents = conn.execute("SELECT * FROM agents").fetchall()
        click.echo(f"=== Life Control Dashboard ===")
        click.echo(f"Registered agents: {len(agents)}")
        for a in agents:
            click.echo(f"  [{a['agent_id']}] {a['name']} | {a['domain']} | {a['status']}")

    @cli.command()
    def fleet():
        conn = get_conn(); init_db(conn)
        agents = conn.execute("SELECT * FROM agents ORDER BY agent_id").fetchall()
        if not agents:
            click.echo("No agents registered.", err=True); sys.exit(1)
        for a in agents:
            click.echo(f"{a['agent_id']}\\t{a['name']}\\t{a['domain']}\\t{a['status']}")

    @cli.command()
    def list():
        conn = get_conn(); init_db(conn)
        goals = conn.execute(
            "SELECT g.id, g.agent_id, g.title, g.priority, a.name "
            "FROM goals g JOIN agents a ON g.agent_id=a.agent_id ORDER BY g.id"
        ).fetchall()
        for g in goals:
            click.echo(f"[{g['id']}] ({g['agent_id']}/{g['name']}) {g['title']} [{g['priority']}]")

    @cli.command()
    @click.argument("agent_id")
    @click.argument("title")
    @click.option("--priority", default="medium",
                  type=click.Choice(["low","medium","high","critical"]))
    def add(agent_id, title, priority):
        conn = get_conn(); init_db(conn)
        row = conn.execute("SELECT 1 FROM agents WHERE agent_id=?", (agent_id,)).fetchone()
        if not row:
            click.echo(f"Unknown agent: {agent_id}", err=True); sys.exit(1)
        conn.execute("INSERT INTO goals(agent_id,title,priority) VALUES(?,?,?)",
                     (agent_id, title, priority))
        conn.commit()
        click.echo(f"Goal added for {agent_id}: {title} [{priority}]")

    @cli.command()
    @click.argument("agent_id")
    @click.argument("metric")
    @click.argument("value", type=int)
    def log(agent_id, metric, value):
        VALID = {"protein","water","workout","expense","meditate"}
        if metric not in VALID:
            click.echo(f"Invalid metric '{metric}'. Must be one of: {', '.join(sorted(VALID))}",
                       err=True); sys.exit(1)
        conn = get_conn(); init_db(conn)
        conn.execute("INSERT INTO logs(agent_id,metric,value) VALUES(?,?,?)",
                     (agent_id, metric, value))
        conn.commit()
        click.echo(f"Logged {metric}={value} for {agent_id}")

    @cli.command()
    @click.argument("agent_id")
    @click.argument("message")
    def notify(agent_id, message):
        conn = get_conn(); init_db(conn)
        row = conn.execute("SELECT 1 FROM agents WHERE agent_id=?", (agent_id,)).fetchone()
        if not row:
            click.echo(f"Unknown agent: {agent_id}", err=True); sys.exit(1)
        # Also write to queue file
        db_dir = DB_PATH.parent
        db_dir.mkdir(parents=True, exist_ok=True)
        queue_file = db_dir / f"notify-queue-{agent_id}.txt"
        with open(queue_file, "a") as f:
            f.write(f"{datetime.datetime.now().isoformat()}|{message}\\n")
        conn.execute("INSERT INTO notifications(agent_id,message) VALUES(?,?)",
                     (agent_id, message))
        conn.commit()
        click.echo(f"Notification queued for {agent_id}: {message}")

    @cli.command()
    @click.argument("agent_id")
    @click.argument("name")
    @click.argument("domain")
    def register(agent_id, name, domain):
        conn = get_conn(); init_db(conn)
        conn.execute(
            "INSERT OR REPLACE INTO agents(agent_id,name,domain,status) VALUES(?,?,?,'active')",
            (agent_id, name, domain))
        conn.commit()
        click.echo(f"Registered agent {agent_id}: {name} ({domain})")

    if __name__ == "__main__":
        cli()
    """, executable=True)

# ── qlog tool ────────────────────────────────────────────────────────────────
write_file("skills/life-control/bin/qlog", """\
    #!/usr/bin/env python3
    \"\"\"Quick-log CLI (qlog) - fast metric entry for Life Control.\"\"\"
    import sys, os, sqlite3, datetime, click
    from pathlib import Path

    DB_PATH = Path(os.environ.get("LC_DB_PATH",
                   str(Path(__file__).parent.parent / "db" / "life-control.db")))
    VALID_METRICS = {"protein", "water", "workout", "expense", "meditate"}

    def get_conn():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    @click.command()
    @click.argument("metric_type")
    @click.argument("value", type=int)
    @click.option("--agent", required=True, help="Agent ID (e.g. oc-001)")
    def qlog(metric_type, value, agent):
        if metric_type not in VALID_METRICS:
            click.echo(
                f"Error: invalid metric '{metric_type}'. "
                f"Accepted: {', '.join(sorted(VALID_METRICS))}", err=True)
            sys.exit(1)
        conn = get_conn()
        # ensure tables exist
        conn.executescript(\"\"\"
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY, name TEXT, domain TEXT,
                status TEXT DEFAULT 'active', created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL, metric TEXT NOT NULL, value INTEGER NOT NULL,
                logged_at TEXT DEFAULT (datetime('now'))
            );
        \"\"\")
        row = conn.execute("SELECT 1 FROM agents WHERE agent_id=?", (agent,)).fetchone()
        if not row:
            click.echo(f"Error: unknown agent '{agent}'", err=True); sys.exit(1)
        conn.execute("INSERT INTO logs(agent_id,metric,value) VALUES(?,?,?)",
                     (agent, metric_type, value))
        conn.commit()
        click.echo(f"[qlog] {metric_type}={value} → {agent}")

    if __name__ == "__main__":
        qlog()
    """, executable=True)

# ── bootstrap.sh ─────────────────────────────────────────────────────────────
write_file("skills/life-control/scripts/bootstrap.sh", """\
    #!/usr/bin/env bash
    set -euo pipefail
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "[bootstrap] Initializing Life Control DB..."
    bash "$SCRIPT_DIR/setup-agents.sh"
    echo "[bootstrap] Bootstrap complete. Run: lc fleet"
    """, executable=True)

# ── setup-agents.sh ───────────────────────────────────────────────────────────
write_file("skills/life-control/scripts/setup-agents.sh", """\
    #!/usr/bin/env bash
    set -euo pipefail
    BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../bin" && pwd)"
    echo "[setup-agents] Reading persona config..."
    # Reads from skills/life-control/references/agents-config.json if present,
    # otherwise requires manual registration via `lc register`.
    CONFIG="$(cd "$(dirname "${BASH_SOURCE[0]}")/../references" && pwd)/agents-config.json"
    if [[ -f "$CONFIG" ]]; then
        echo "[setup-agents] Found agents-config.json, auto-registering..."
        python3 - <<'PYEOF'
    import json, subprocess, os, sys
    from pathlib import Path
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "references" / "agents-config.json"
    bin_dir = script_dir.parent / "bin"
    lc = str(bin_dir / "lc")
    data = json.loads(config_path.read_text())
    for agent in data.get("agents", []):
        result = subprocess.run(
            [sys.executable, lc, "register", agent["agent_id"], agent["name"], agent["domain"]],
            capture_output=True, text=True
        )
        print(result.stdout.strip())
        if result.returncode != 0:
            print(result.stderr.strip(), file=sys.stderr)
    PYEOF
    else
        echo "[setup-agents] No agents-config.json found."
        echo "[setup-agents] Please create references/agents-config.json or register agents manually."
    fi
    """, executable=True)

# ── Routine scripts ───────────────────────────────────────────────────────────
ROUTINES = {
    "morning-alignment": "Morning Alignment",
    "body-protocol": "Body Protocol",
    "financial-pulse": "Financial Pulse",
    "social-radar": "Social Radar",
    "work-priming": "Work Priming",
    "shutdown": "Shutdown",
}
for slug, title in ROUTINES.items():
    write_file(f"skills/life-control/routines/{slug}.sh", f"""\
        #!/usr/bin/env bash
        set -euo pipefail
        AGENT_ID="${{1:?Usage: {slug}.sh <agent_id>}}"
        LOG_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")/../logs" && pwd)"
        mkdir -p "$LOG_DIR"
        LOG_FILE="$LOG_DIR/${{AGENT_ID}}-{slug}.log"
        echo "[{title}] Running for agent $AGENT_ID at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_FILE"
        echo "[{title}] Routine complete." | tee -a "$LOG_FILE"
        """, executable=True)

# ── telegram-sender.sh ────────────────────────────────────────────────────────
write_file("skills/life-control/scripts/telegram-sender.sh", """\
    #!/usr/bin/env bash
    # Sends queued notifications to Telegram bots.
    # Requires: TELEGRAM_CHAT_ID, BOT_TOKEN_<AGENT_ID_UPPER> env vars.
    echo "[telegram-sender] Dry run: no tokens configured."
    """, executable=True)

# ── crontab-template.txt ──────────────────────────────────────────────────────
write_file("skills/life-control/templates/crontab-template.txt", """\
    # Life Control Cron Schedule Template
    # Copy relevant lines to your crontab (crontab -e)
    #
    # Morning Alignment  – 06:00 daily
    0 6 * * * bash /workspace/skills/life-control/routines/morning-alignment.sh oc-001
    # Body Protocol      – 07:00 daily
    0 7 * * * bash /workspace/skills/life-control/routines/body-protocol.sh oc-001
    # Financial Pulse    – 09:00 weekdays
    0 9 * * 1-5 bash /workspace/skills/life-control/routines/financial-pulse.sh oc-002
    # Social Radar       – 12:00 daily
    0 12 * * * bash /workspace/skills/life-control/routines/social-radar.sh oc-003
    # Work Priming       – 08:30 weekdays
    30 8 * * 1-5 bash /workspace/skills/life-control/routines/work-priming.sh oc-002
    # Shutdown           – 22:00 daily
    0 22 * * * bash /workspace/skills/life-control/routines/shutdown.sh oc-001
    # Telegram sender    – every 30 minutes
    */30 * * * * bash /workspace/skills/life-control/scripts/telegram-sender.sh
    """)

# ── Distractor files ──────────────────────────────────────────────────────────
write_file("docs/archive/old-setup-v1.sh", """\
    #!/bin/bash
    # DEPRECATED: do not use
    echo "This is the old v1 setup. Use bootstrap.sh instead."
    """)

write_file("docs/archive/legacy-personas.json", """\
    [
      {"id": "agent-alpha", "role": "wellness", "deprecated": true},
      {"id": "agent-beta",  "role": "finance",  "deprecated": true}
    ]
    """)

write_file("docs/onboarding/getting-started.txt", """\
    Welcome to the Life Control system.
    Please refer to SKILL.md for the current setup instructions.
    This document is for HR onboarding only.
    """)

write_file("config/legacy/agents.yaml", """\
    # LEGACY - not used by current CLI
    agents:
      - id: zeus
        domain: all
    """)

write_file("config/env/sample.env", """\
    # Sample environment variables
    # TELEGRAM_CHAT_ID=123456789
    # BOT_TOKEN_OC_001=xxx
    # LC_DB_PATH=/workspace/skills/life-control/db/life-control.db
    """)

write_file("tests/unit/test_placeholder.py", """\
    # Unit tests placeholder - not yet implemented
    def test_noop():
        pass
    """)

write_file("tests/integration/test_integration_placeholder.py", """\
    # Integration tests placeholder
    pass
    """)

write_file("config/legacy/cron.old.txt", """\
    # old cron - replaced by crontab-template.txt
    0 8 * * * /usr/bin/python3 /opt/old-lc/run.py
    """)

write_file("skills/life-control/logs/.gitkeep", "")
write_file("skills/life-control/db/.gitkeep", "")

# ── Intentionally incomplete/wrong agents-config (trap: wrong agent IDs) ─────
# NOTE: We do NOT create references/agents-config.json here.
# The agent must read openclaw.md to discover correct persona details and create it.

print("Workspace scaffold complete.")
print(f"Root: {WORKSPACE}")