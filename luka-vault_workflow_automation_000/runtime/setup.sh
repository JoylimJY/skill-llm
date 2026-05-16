#!/usr/bin/env bash
set -e

export PATH="/root/.cargo/bin:/root/.local/bin:$PATH"
cd /workspace

echo "=== Setting up ResearchVault environment ==="

# Clone the researchvault repository
if [ ! -d "researchvault" ]; then
    git clone https://github.com/p-i-/researchvault.git researchvault 2>/dev/null || \
    git clone https://github.com/openclaw/researchvault.git researchvault 2>/dev/null || \
    true
fi

# If clone failed or repo doesn't have expected structure, bootstrap a minimal one
if [ ! -f "researchvault/scripts/vault.py" ]; then
    echo "Building minimal ResearchVault scaffold..."
    mkdir -p researchvault/scripts
    mkdir -p researchvault/src/researchvault

    # Write pyproject.toml
    cat > researchvault/pyproject.toml << 'PYPROJECT'
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "researchvault"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
    "numpy>=1.26",
]

[tool.setuptools.packages.find]
where = ["src"]
PYPROJECT

    # Write the vault.py CLI script (functional minimal implementation)
    cat > researchvault/scripts/vault.py << 'VAULTPY'
#!/usr/bin/env python3
"""ResearchVault CLI — minimal functional implementation for sandbox."""
import click
import sqlite3
import json
import hashlib
import datetime
from pathlib import Path

DB_DIR = Path.home() / ".researchvault"
DB_DIR.mkdir(exist_ok=True)

def get_db(project_id: str) -> sqlite3.Connection:
    db_path = DB_DIR / f"{project_id}.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn

def _ensure_schema(conn: sqlite3.Connection):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        objective TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS artifacts (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        source TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        ingested_at TEXT NOT NULL,
        raw_content TEXT
    );
    CREATE TABLE IF NOT EXISTS findings (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        artifact_id TEXT NOT NULL,
        summary TEXT NOT NULL,
        confidence TEXT DEFAULT 'MEDIUM',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS links (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        finding_a TEXT NOT NULL,
        finding_b TEXT NOT NULL,
        rationale TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS verification_missions (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        finding_id TEXT NOT NULL,
        mission_type TEXT NOT NULL,
        priority TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        created_at TEXT NOT NULL
    );
    """)
    conn.commit()

@click.group()
def cli():
    """ResearchVault: Autonomous research state manager."""
    pass

@cli.command()
@click.option("--id", "project_id", required=True, help="Unique project identifier")
@click.option("--name", required=True, help="Project name")
@click.option("--objective", required=True, help="Research objective")
def init(project_id, name, objective):
    """Initialize a new research project vault."""
    conn = get_db(project_id)
    now = datetime.datetime.utcnow().isoformat()
    try:
        conn.execute(
            "INSERT INTO projects (id, name, objective, created_at) VALUES (?, ?, ?, ?)",
            (project_id, name, objective, now)
        )
        conn.commit()
        click.echo(f"✓ Vault initialized: [{project_id}] '{name}'")
        click.echo(f"  Objective: {objective}")
    except sqlite3.IntegrityError:
        click.echo(f"⚠ Project '{project_id}' already exists.")
    finally:
        conn.close()

@cli.command()
@click.argument("source")
@click.option("--id", "project_id", required=True, help="Project ID to attach artifact to")
def scuttle(source, project_id):
    """Ingest a source (file path or URL) as an artifact into the vault."""
    import urllib.request
    conn = get_db(project_id)

    # Check project exists
    proj = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not proj:
        click.echo(f"✗ Project '{project_id}' not found. Run `init` first.", err=True)
        raise SystemExit(1)

    # Load content
    if source.startswith("http://") or source.startswith("https://"):
        try:
            with urllib.request.urlopen(source, timeout=10) as r:
                raw = r.read().decode("utf-8", errors="replace")
        except Exception as e:
            raw = f"[fetch error: {e}]"
    else:
        p = Path(source)
        if p.exists():
            raw = p.read_text(errors="replace")
        else:
            click.echo(f"✗ File not found: {source}", err=True)
            raise SystemExit(1)

    content_hash = hashlib.sha256(raw.encode()).hexdigest()
    artifact_id = f"art-{content_hash[:12]}"
    now = datetime.datetime.utcnow().isoformat()

    # Deduplicate
    existing = conn.execute("SELECT id FROM artifacts WHERE content_hash=? AND project_id=?",
                            (content_hash, project_id)).fetchone()
    if existing:
        click.echo(f"⚠ Duplicate artifact skipped: {source}")
        conn.close()
        return

    conn.execute(
        "INSERT INTO artifacts (id, project_id, source, content_hash, ingested_at, raw_content) VALUES (?,?,?,?,?,?)",
        (artifact_id, project_id, source, content_hash, now, raw[:50000])
    )

    # Auto-extract findings from content (naive line-based extraction)
    lines = [l.strip() for l in raw.splitlines() if len(l.strip()) > 30]
    finding_count = 0
    for i, line in enumerate(lines[:40]):
        # Infer confidence
        conf = "MEDIUM"
        if "HIGH" in line.upper(): conf = "HIGH"
        elif "LOW" in line.upper(): conf = "LOW"

        fid = f"fnd-{content_hash[:8]}-{i:03d}"
        conn.execute(
            "INSERT OR IGNORE INTO findings (id, project_id, artifact_id, summary, confidence, created_at) VALUES (?,?,?,?,?,?)",
            (fid, project_id, artifact_id, line[:500], conf, now)
        )
        finding_count += 1

    conn.commit()
    conn.close()
    click.echo(f"✓ Ingested artifact: {source}")
    click.echo(f"  Artifact ID: {artifact_id}")
    click.echo(f"  Findings extracted: {finding_count}")

@cli.command()
@click.option("--id", "project_id", required=True, help="Project ID to synthesize")
def synthesize(project_id):
    """Discover and link related findings using content similarity."""
    conn = get_db(project_id)

    proj = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not proj:
        click.echo(f"✗ Project '{project_id}' not found.", err=True)
        raise SystemExit(1)

    findings = conn.execute(
        "SELECT id, summary FROM findings WHERE project_id=?", (project_id,)
    ).fetchall()

    if len(findings) < 2:
        click.echo("⚠ Not enough findings to synthesize links.")
        conn.close()
        return

    # Naive similarity: shared significant words
    def tokenize(text):
        import re
        words = set(re.findall(r'\b[a-z]{4,}\b', text.lower()))
        stopwords = {'with','that','this','from','have','been','will','they','their',
                     'also','more','into','than','such','when','were','what','which'}
        return words - stopwords

    now = datetime.datetime.utcnow().isoformat()
    link_count = 0
    for i in range(len(findings)):
        for j in range(i + 1, len(findings)):
            fa, fb = findings[i], findings[j]
            ta, tb = tokenize(fa["summary"]), tokenize(fb["summary"])
            overlap = ta & tb
            if len(overlap) >= 3:
                link_id = f"lnk-{fa['id'][-6:]}-{fb['id'][-6:]}"
                rationale = f"Shared concepts: {', '.join(sorted(overlap)[:5])}"
                conn.execute(
                    "INSERT OR IGNORE INTO links (id, project_id, finding_a, finding_b, rationale, created_at) VALUES (?,?,?,?,?,?)",
                    (link_id, project_id, fa["id"], fb["id"], rationale, now)
                )
                link_count += 1

    conn.commit()
    conn.close()
    click.echo(f"✓ Synthesis complete for project '{project_id}'")
    click.echo(f"  Links discovered: {link_count}")

@cli.group()
def verify():
    """Verification mission management."""
    pass

@verify.command("plan")
@click.option("--id", "project_id", required=True, help="Project ID")
def verify_plan(project_id):
    """Generate verification missions for low-confidence findings."""
    conn = get_db(project_id)

    proj = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not proj:
        click.echo(f"✗ Project '{project_id}' not found.", err=True)
        raise SystemExit(1)

    low_conf = conn.execute(
        "SELECT id, summary, confidence FROM findings WHERE project_id=? AND confidence IN ('LOW','MEDIUM')",
        (project_id,)
    ).fetchall()

    now = datetime.datetime.utcnow().isoformat()
    mission_count = 0
    for f in low_conf:
        mid = f"vm-{f['id'][-8:]}"
        priority = "HIGH" if f["confidence"] == "LOW" else "NORMAL"
        conn.execute(
            "INSERT OR IGNORE INTO verification_missions (id, project_id, finding_id, mission_type, priority, status, created_at) VALUES (?,?,?,?,?,?,?)",
            (mid, project_id, f["id"], "FACT_CHECK", priority, "PENDING", now)
        )
        mission_count += 1

    conn.commit()

    # Export plan to JSON for downstream consumption
    missions = conn.execute(
        "SELECT * FROM verification_missions WHERE project_id=?", (project_id,)
    ).fetchall()

    plan = {
        "project_id": project_id,
        "generated_at": now,
        "total_missions": mission_count,
        "missions": [dict(m) for m in missions]
    }

    output_path = DB_DIR / f"{project_id}_verification_plan.json"
    output_path.write_text(json.dumps(plan, indent=2))

    conn.close()
    click.echo(f"✓ Verification plan generated for '{project_id}'")
    click.echo(f"  Missions created: {mission_count}")
    click.echo(f"  Plan saved: {output_path}")

if __name__ == "__main__":
    cli()
VAULTPY

    chmod +x researchvault/scripts/vault.py
fi

# Initialize the uv environment inside the researchvault directory
cd /workspace/researchvault
uv venv --python 3.13 2>/dev/null || uv venv
uv pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "=== ResearchVault environment ready ==="
echo "Run commands like: cd /workspace/researchvault && uv run python scripts/vault.py init --id ..."