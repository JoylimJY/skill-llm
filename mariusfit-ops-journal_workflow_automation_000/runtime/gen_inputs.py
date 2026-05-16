import os
import random
import json
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create deeply nested distractor directory structure
dirs = [
    "scripts",
    "config/nginx",
    "config/postgres",
    "config/redis",
    "logs/archive/2024",
    "logs/archive/2023",
    "logs/live",
    "monitoring/alerts",
    "monitoring/dashboards",
    "deployments/history",
    "deployments/rollbacks",
    "docs/runbooks",
    "docs/architecture",
    "infra/terraform",
    "infra/ansible",
    "backups/daily",
    "backups/weekly",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Create distractor files
distractor_files = {
    "config/nginx/nginx.conf": "worker_processes 4;\nevents { worker_connections 1024; }\n",
    "config/postgres/pg_hba.conf": "# TYPE  DATABASE  USER  ADDRESS  METHOD\nlocal   all       all            trust\n",
    "config/redis/redis.conf": "maxmemory 256mb\nmaxmemory-policy allkeys-lru\n",
    "logs/archive/2024/app.log.gz.info": "archived log - 2024-01-15 through 2024-06-30\n",
    "logs/archive/2023/db.log.gz.info": "archived db log - 2023-01-01 through 2023-12-31\n",
    "logs/live/error.log": "[ERROR] 2024-11-01 connection timeout db-primary\n[WARN]  2024-11-01 slow query detected\n",
    "monitoring/alerts/thresholds.yaml": "cpu_alert: 85\nmem_alert: 90\ndisk_alert: 80\nlatency_ms: 500\n",
    "monitoring/dashboards/overview.json": json.dumps({"dashboard": "ops-overview", "panels": ["cpu", "mem", "latency", "errors"]}),
    "deployments/history/v2.3.1.txt": "Deployed 2024-10-28 14:00 UTC\nService: payment-api\nResult: success\n",
    "deployments/history/v2.3.0.txt": "Deployed 2024-10-14 10:30 UTC\nService: payment-api\nResult: success\n",
    "deployments/rollbacks/v2.2.9.txt": "Rollback executed 2024-09-05 03:15 UTC\nReason: memory leak in transaction handler\n",
    "docs/runbooks/db_failover.md": "# DB Failover Runbook\n1. Check replication lag\n2. Promote replica\n3. Update DNS\n",
    "docs/runbooks/incident_response.md": "# Incident Response\n1. Identify impacted services\n2. Notify stakeholders\n3. Investigate root cause\n",
    "docs/architecture/system_diagram.txt": "payment-api --> postgres-primary --> postgres-replica\npayment-api --> redis-cache\n",
    "infra/terraform/main.tf": 'provider "aws" {\n  region = "us-east-1"\n}\n',
    "infra/ansible/inventory.ini": "[db_servers]\ndb-primary ansible_host=10.0.1.10\ndb-replica ansible_host=10.0.1.11\n",
    "backups/daily/manifest.txt": "backup_20241101_0300.tar.gz  OK\nbackup_20241102_0300.tar.gz  OK\n",
    "backups/weekly/manifest.txt": "weekly_backup_20241027.tar.gz  OK\n",
}

for fpath, content in distractor_files.items():
    full_path = workspace / fpath
    full_path.write_text(content)

# ---- Create the MAIN journal script ----
journal_script = r'''#!/usr/bin/env python3
"""ops-journal — Automated Ops Logging & Incident Timeline for OpenClaw"""

import sqlite3
import json
import csv
import sys
import os
import re
import click
from datetime import datetime, timedelta
from pathlib import Path

STORAGE_DIR = Path.home() / ".openclaw" / "workspace" / "ops-journal"
DB_PATH = STORAGE_DIR / "journal.db"
INCIDENTS_DIR = STORAGE_DIR / "incidents"

CATEGORIES = ["deploy", "incident", "config", "maintenance", "security", "note"]
SEVERITIES = ["info", "warn", "high", "critical"]

CATEGORY_ICONS = {
    "deploy": "🚀",
    "incident": "🔥",
    "config": "⚙️",
    "maintenance": "🔧",
    "security": "🔒",
    "note": "📝",
}

SEVERITY_COLORS = {
    "info": "\033[37m",
    "warn": "\033[33m",
    "high": "\033[91m",
    "critical": "\033[31m",
}
RESET = "\033[0m"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            message TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'note',
            severity TEXT NOT NULL DEFAULT 'info',
            tags TEXT DEFAULT '',
            incident_id TEXT DEFAULT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'high',
            status TEXT NOT NULL DEFAULT 'open',
            opened_at TEXT NOT NULL,
            resolved_at TEXT DEFAULT NULL,
            resolution TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()


def next_incident_id():
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) as cnt FROM incidents").fetchone()
    conn.close()
    return f"INC-{row['cnt'] + 1:03d}"


def parse_since(since_str):
    if not since_str:
        return None
    m = re.match(r'^(\d+)([dwm])$', since_str)
    if not m:
        raise ValueError(f"Invalid --since format: {since_str}. Use Nd, Nw, or Nm.")
    n, unit = int(m.group(1)), m.group(2)
    now = datetime.utcnow()
    if unit == 'd':
        return now - timedelta(days=n)
    elif unit == 'w':
        return now - timedelta(weeks=n)
    elif unit == 'm':
        return now - timedelta(days=30 * n)


@click.group()
def cli():
    """ops-journal — Automated Ops Logging & Incident Timeline"""
    pass


@cli.command()
def init():
    """Initialize the journal database."""
    init_db()
    click.echo("✅ ops-journal initialized.")
    click.echo(f"   Storage: {STORAGE_DIR}")


@cli.command()
@click.argument("message")
@click.option("--category", "-c", default="note", type=click.Choice(CATEGORIES))
@click.option("--severity", "-s", default="info", type=click.Choice(SEVERITIES))
@click.option("--tags", default="", help="Comma-separated tags")
@click.option("--incident-id", default=None, help="Associate with incident ID")
def log(message, category, severity, tags, incident_id):
    """Create a journal entry."""
    init_db()
    ts = datetime.utcnow().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO entries (timestamp, message, category, severity, tags, incident_id) VALUES (?,?,?,?,?,?)",
        (ts, message, category, severity, tags, incident_id)
    )
    conn.commit()
    conn.close()
    icon = CATEGORY_ICONS.get(category, "📋")
    color = SEVERITY_COLORS.get(severity, "")
    click.echo(f"{color}{icon} [{severity.upper()}] {category}: {message}{RESET}")


@cli.group()
def incident():
    """Incident management commands."""
    pass


@incident.command("open")
@click.argument("description")
@click.option("--severity", "-s", default="high", type=click.Choice(SEVERITIES))
def incident_open(description, severity):
    """Open a new incident."""
    init_db()
    inc_id = next_incident_id()
    ts = datetime.utcnow().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO incidents (id, description, severity, status, opened_at) VALUES (?,?,?,?,?)",
        (inc_id, description, severity, "open", ts)
    )
    # Also log it as a journal entry
    conn.execute(
        "INSERT INTO entries (timestamp, message, category, severity, tags, incident_id) VALUES (?,?,?,?,?,?)",
        (ts, f"Incident opened: {description}", "incident", severity, "incident", inc_id)
    )
    conn.commit()
    conn.close()
    inc_path = INCIDENTS_DIR / f"{inc_id}.md"
    inc_path.write_text(f"# {inc_id}: {description}\n\n**Status:** open\n**Severity:** {severity}\n**Opened:** {ts}\n\n## Timeline\n\n- {ts} — Incident opened: {description}\n")
    click.echo(f"🔥 Incident {inc_id} opened: {description} [severity={severity}]")
    click.echo(f"   File: {inc_path}")


@incident.command("resolve")
@click.argument("incident_id")
@click.argument("resolution")
def incident_resolve(incident_id, resolution):
    """Resolve an incident."""
    init_db()
    ts = datetime.utcnow().isoformat()
    conn = get_db()
    row = conn.execute("SELECT * FROM incidents WHERE id=?", (incident_id,)).fetchone()
    if not row:
        click.echo(f"❌ Incident {incident_id} not found.", err=True)
        sys.exit(1)
    conn.execute(
        "UPDATE incidents SET status='resolved', resolved_at=?, resolution=? WHERE id=?",
        (ts, resolution, incident_id)
    )
    conn.execute(
        "INSERT INTO entries (timestamp, message, category, severity, tags, incident_id) VALUES (?,?,?,?,?,?)",
        (ts, f"Incident resolved: {resolution}", "incident", "info", "resolved", incident_id)
    )
    conn.commit()
    conn.close()
    inc_path = INCIDENTS_DIR / f"{incident_id}.md"
    if inc_path.exists():
        content = inc_path.read_text()
        content += f"\n## Resolution\n\n{resolution}\n\n**Resolved at:** {ts}\n"
        inc_path.write_text(content)
    click.echo(f"✅ Incident {incident_id} resolved.")
    click.echo(f"   Resolution: {resolution}")


@incident.command("list")
@click.option("--status", default="all", type=click.Choice(["open", "resolved", "all"]))
def incident_list(status):
    """List incidents."""
    init_db()
    conn = get_db()
    if status == "all":
        rows = conn.execute("SELECT * FROM incidents ORDER BY opened_at DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM incidents WHERE status=? ORDER BY opened_at DESC", (status,)).fetchall()
    conn.close()
    if not rows:
        click.echo("No incidents found.")
        return
    for r in rows:
        color = SEVERITY_COLORS.get(r["severity"], "")
        click.echo(f"{color}{r['id']} [{r['status'].upper()}] {r['description']} (severity={r['severity']}){RESET}")


@incident.command("show")
@click.argument("incident_id")
def incident_show(incident_id):
    """Show incident details."""
    init_db()
    conn = get_db()
    row = conn.execute("SELECT * FROM incidents WHERE id=?", (incident_id,)).fetchone()
    if not row:
        click.echo(f"❌ Incident {incident_id} not found.", err=True)
        sys.exit(1)
    entries = conn.execute(
        "SELECT * FROM entries WHERE incident_id=? ORDER BY timestamp ASC", (incident_id,)
    ).fetchall()
    conn.close()
    click.echo(f"\n{'='*50}")
    click.echo(f"Incident: {row['id']}")
    click.echo(f"Description: {row['description']}")
    click.echo(f"Severity: {row['severity']}")
    click.echo(f"Status: {row['status']}")
    click.echo(f"Opened: {row['opened_at']}")
    if row['resolved_at']:
        click.echo(f"Resolved: {row['resolved_at']}")
        click.echo(f"Resolution: {row['resolution']}")
    click.echo(f"\nLinked Events ({len(entries)}):")
    for e in entries:
        click.echo(f"  [{e['timestamp']}] {e['message']}")


@cli.command()
@click.argument("query", required=False, default=None)
@click.option("--category", "-c", default=None, type=click.Choice(CATEGORIES))
@click.option("--severity", "-s", default=None, type=click.Choice(SEVERITIES))
@click.option("--since", default=None)
@click.option("--limit", "-n", default=50, type=int)
def search(query, category, severity, since, limit):
    """Search journal entries."""
    init_db()
    conn = get_db()
    sql = "SELECT * FROM entries WHERE 1=1"
    params = []
    if query:
        sql += " AND message LIKE ?"
        params.append(f"%{query}%")
    if category:
        sql += " AND category=?"
        params.append(category)
    if severity:
        sql += " AND severity=?"
        params.append(severity)
    if since:
        dt = parse_since(since)
        sql += " AND timestamp >= ?"
        params.append(dt.isoformat())
    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    if not rows:
        click.echo("No entries found.")
        return
    for r in rows:
        icon = CATEGORY_ICONS.get(r["category"], "📋")
        color = SEVERITY_COLORS.get(r["severity"], "")
        click.echo(f"{color}{icon} [{r['timestamp']}] [{r['severity'].upper()}] {r['category']}: {r['message']}{RESET}")


@cli.command()
@click.option("--period", default="week", type=click.Choice(["day", "week", "month"]))
@click.option("--json", "output_json", is_flag=True, default=False)
def summary(period, output_json):
    """Generate period summary."""
    init_db()
    deltas = {"day": timedelta(days=1), "week": timedelta(weeks=1), "month": timedelta(days=30)}
    since_dt = datetime.utcnow() - deltas[period]
    conn = get_db()
    entries = conn.execute(
        "SELECT * FROM entries WHERE timestamp >= ? ORDER BY timestamp ASC",
        (since_dt.isoformat(),)
    ).fetchall()
    incidents = conn.execute(
        "SELECT * FROM incidents WHERE opened_at >= ? ORDER BY opened_at ASC",
        (since_dt.isoformat(),)
    ).fetchall()
    conn.close()

    by_cat = {}
    by_sev = {}
    for e in entries:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1
        by_sev[e["severity"]] = by_sev.get(e["severity"], 0) + 1

    data = {
        "period": period,
        "since": since_dt.isoformat(),
        "total_entries": len(entries),
        "by_category": by_cat,
        "by_severity": by_sev,
        "open_incidents": sum(1 for i in incidents if i["status"] == "open"),
        "resolved_incidents": sum(1 for i in incidents if i["status"] == "resolved"),
        "incidents": [
            {
                "id": i["id"],
                "description": i["description"],
                "severity": i["severity"],
                "status": i["status"],
            }
            for i in incidents
        ],
    }

    if output_json:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"\n📊 Summary ({period})")
        click.echo(f"  Period: {since_dt.strftime('%Y-%m-%d')} → now")
        click.echo(f"  Total entries: {data['total_entries']}")
        click.echo(f"  By category: {data['by_category']}")
        click.echo(f"  By severity: {data['by_severity']}")
        click.echo(f"  Incidents: {data['open_incidents']} open, {data['resolved_incidents']} resolved")


@cli.command()
@click.argument("incident_id")
@click.option("--format", "fmt", default="markdown", type=click.Choice(["markdown", "json"]))
def timeline(incident_id, fmt):
    """Generate incident timeline."""
    init_db()
    conn = get_db()
    row = conn.execute("SELECT * FROM incidents WHERE id=?", (incident_id,)).fetchone()
    if not row:
        click.echo(f"❌ Incident {incident_id} not found.", err=True)
        sys.exit(1)
    entries = conn.execute(
        "SELECT * FROM entries WHERE incident_id=? ORDER BY timestamp ASC", (incident_id,)
    ).fetchall()
    conn.close()

    if fmt == "json":
        data = {
            "incident_id": row["id"],
            "description": row["description"],
            "severity": row["severity"],
            "status": row["status"],
            "opened_at": row["opened_at"],
            "resolved_at": row["resolved_at"],
            "resolution": row["resolution"],
            "timeline": [
                {
                    "timestamp": e["timestamp"],
                    "message": e["message"],
                    "category": e["category"],
                    "severity": e["severity"],
                }
                for e in entries
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"\n# Timeline: {row['id']}")
        click.echo(f"\n**Description:** {row['description']}")
        click.echo(f"**Severity:** {row['severity']}")
        click.echo(f"**Status:** {row['status']}")
        click.echo(f"**Opened:** {row['opened_at']}")
        if row['resolved_at']:
            click.echo(f"**Resolved:** {row['resolved_at']}")
        click.echo(f"\n## Events\n")
        for e in entries:
            click.echo(f"- `{e['timestamp']}` **[{e['severity'].upper()}]** {e['message']}")
        if row["resolution"]:
            click.echo(f"\n## Resolution\n\n{row['resolution']}")


@cli.command("export")
@click.option("--format", "fmt", default="markdown", type=click.Choice(["markdown", "json", "csv"]))
@click.option("--since", default=None)
@click.option("--output", "-o", default=None, help="Output file path")
def export_cmd(fmt, since, output):
    """Export journal entries."""
    init_db()
    conn = get_db()
    sql = "SELECT * FROM entries WHERE 1=1"
    params = []
    if since:
        dt = parse_since(since)
        sql += " AND timestamp >= ?"
        params.append(dt.isoformat())
    sql += " ORDER BY timestamp ASC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    if fmt == "json":
        data = [dict(r) for r in rows]
        content = json.dumps(data, indent=2)
    elif fmt == "csv":
        import io
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "timestamp", "message", "category", "severity", "tags", "incident_id"])
        for r in rows:
            writer.writerow([r["id"], r["timestamp"], r["message"], r["category"], r["severity"], r["tags"], r["incident_id"]])
        content = buf.getvalue()
    else:  # markdown
        lines = ["# Ops Journal Export\n"]
        for r in rows:
            icon = CATEGORY_ICONS.get(r["category"], "📋")
            lines.append(f"## {icon} [{r['timestamp']}] {r['category'].upper()}")
            lines.append(f"**Severity:** {r['severity']}  ")
            lines.append(f"**Message:** {r['message']}  ")
            if r["tags"]:
                lines.append(f"**Tags:** {r['tags']}  ")
            if r["incident_id"]:
                lines.append(f"**Incident:** {r['incident_id']}  ")
            lines.append("")
        content = "\n".join(lines)

    if output:
        Path(output).write_text(content)
        click.echo(f"✅ Exported {len(rows)} entries to {output}")
    else:
        click.echo(content)


@cli.command()
@click.option("--period", default="month", type=click.Choice(["day", "week", "month"]))
def stats(period):
    """Show journal statistics."""
    init_db()
    deltas = {"day": timedelta(days=1), "week": timedelta(weeks=1), "month": timedelta(days=30)}
    since_dt = datetime.utcnow() - deltas[period]
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as cnt FROM entries WHERE timestamp >= ?", (since_dt.isoformat(),)).fetchone()["cnt"]
    by_cat = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM entries WHERE timestamp >= ? GROUP BY category",
        (since_dt.isoformat(),)
    ).fetchall()
    inc_total = conn.execute("SELECT COUNT(*) as cnt FROM incidents WHERE opened_at >= ?", (since_dt.isoformat(),)).fetchone()["cnt"]
    inc_open = conn.execute("SELECT COUNT(*) as cnt FROM incidents WHERE opened_at >= ? AND status='open'", (since_dt.isoformat(),)).fetchone()["cnt"]
    conn.close()
    click.echo(f"\n📈 Stats ({period})")
    click.echo(f"  Total entries: {total}")
    for row in by_cat:
        click.echo(f"  {row['category']}: {row['cnt']}")
    click.echo(f"  Incidents: {inc_total} total, {inc_open} open")


if __name__ == "__main__":
    cli()
'''

script_path = workspace / "scripts" / "journal.py"
script_path.write_text(journal_script)
os.chmod(script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# Create a SKILL.md
skill_md_content = open("/workspace/scripts/journal.py").read()  # already written above
skill_path = workspace / "SKILL.md"
# Write the actual SKILL.md content (abbreviated reference)
skill_path.write_text("""# ops-journal — Automated Ops Logging & Incident Timeline for OpenClaw

Structured operational journal that captures deployments, incidents, changes, and decisions.

## Quick Start
```bash
python3 scripts/journal.py init
python3 scripts/journal.py log "message" --category deploy
python3 scripts/journal.py incident open "description" --severity high
python3 scripts/journal.py incident resolve INC-001 "resolution text"
python3 scripts/journal.py search "query" --since 7d
python3 scripts/journal.py summary --period week
python3 scripts/journal.py timeline INC-001
python3 scripts/journal.py export --format markdown --since 30d
```

## Entry Categories
deploy | incident | config | maintenance | security | note

## Severity Levels
info | warn | high | critical

## Commands

### log
python3 scripts/journal.py log "message" [--category CAT] [--severity SEV] [--tags tag1,tag2]

### incident
python3 scripts/journal.py incident open "description" [--severity SEV]
python3 scripts/journal.py incident resolve ID "resolution"
python3 scripts/journal.py incident list [--status open|resolved|all]
python3 scripts/journal.py incident show ID

### search
python3 scripts/journal.py search [query] [--category CAT] [--severity SEV] [--since Nd|Nw|Nm] [--limit N]

### summary
python3 scripts/journal.py summary [--period day|week|month] [--json]

### timeline
python3 scripts/journal.py timeline ID [--format markdown|json]

### export
python3 scripts/journal.py export [--format markdown|json|csv] [--since Nd] [--output file]

### stats
python3 scripts/journal.py stats [--period month]

## Storage
All data stored in ~/.openclaw/workspace/ops-journal/
- journal.db — SQLite database
- incidents/ — Individual incident files (markdown)
""")

print("Workspace setup complete.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f}")