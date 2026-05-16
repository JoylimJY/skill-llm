import os
import json
import random
import stat
import datetime
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory skeleton ────────────────────────────────────────────────
dirs = [
    "scripts",
    "tasks",
    "logs",
    "reports/2024/Q1",
    "reports/2024/Q2",
    "data/raw/compounds",
    "data/processed",
    "archive/old_runs",
    "config",
    "docs",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────
distractors = {
    "logs/pipeline.log": "2024-06-01 INFO  Starting compound screener\n2024-06-01 ERROR Timeout on batch 7\n",
    "reports/2024/Q1/summary.csv": "compound_id,score\nCMP-001,0.87\nCMP-002,0.54\n",
    "reports/2024/Q2/summary.csv": "compound_id,score\nCMP-100,0.91\nCMP-101,0.33\n",
    "data/raw/compounds/library_v3.tsv": "\t".join(["id","smiles","mw","logp"]) + "\n" +
        "\t".join(["CMP-200","CC(=O)Oc1ccccc1C(=O)O","180.16","1.19"]) + "\n",
    "data/processed/.gitkeep": "",
    "archive/old_runs/run_2023_q4.tar.gz.stub": "placeholder – real archive on NAS",
    "docs/onboarding.md": "# Onboarding\nSee confluence for details.\n",
    "tests/unit/test_parser.py": "def test_noop(): assert True\n",
    "tests/integration/test_pipeline.py": "def test_noop(): assert True\n",
    "config/db_credentials.env.EXAMPLE": "DB_HOST=localhost\nDB_PORT=5432\nDB_NAME=screening\n",
    "data/raw/compounds/rejected_batch.jsonl": json.dumps({"id": "CMP-999", "reason": "purity < 0.95"}) + "\n",
}
for rel, content in distractors.items():
    p = WORKSPACE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── config.env.example (the real skill artifact) ─────────────────────
config_example = """\
# queue-task configuration example
# Copy this file to config.env and fill in values.

WORKSPACE_DIR=/workspace
TASKS_DIR=tasks
BATCH_SIZE=10
LOCK_STALE_MINUTES=15
CRON_EXPR=*/5 * * * *
CRON_TZ=UTC
DELIVERY_MODE=sequential
AGENT_ID=agent-default
"""
(WORKSPACE / "config.env.example").write_text(config_example)

# ── queue_task.py script (the skill's main script) ───────────────────
queue_task_script = r'''#!/usr/bin/env python3
"""
queue-task helper  –  durable, resumable, idempotent batch jobs.
"""
import sys, os, json, time, pathlib, datetime, textwrap
from pathlib import Path

def load_config():
    cfg = {}
    env_path = Path(__file__).parent.parent / "config.env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    # also honour actual env vars (override)
    for k in ("WORKSPACE_DIR","TASKS_DIR","BATCH_SIZE","LOCK_STALE_MINUTES",
               "CRON_EXPR","CRON_TZ","DELIVERY_MODE","AGENT_ID"):
        if k in os.environ:
            cfg[k] = os.environ[k]
    return cfg

def task_dir(cfg, slug):
    ws = Path(cfg.get("WORKSPACE_DIR", "/workspace"))
    td = cfg.get("TASKS_DIR", "tasks")
    return ws / td / slug

def cmd_init(slug):
    cfg = load_config()
    d = task_dir(cfg, slug)
    d.mkdir(parents=True, exist_ok=True)
    # create state files if missing
    for fname in ("queue.jsonl","done.jsonl","failed.jsonl"):
        f = d / fname
        if not f.exists():
            f.write_text("")
    if not (d / "progress.json").exists():
        (d / "progress.json").write_text(json.dumps({
            "slug": slug,
            "total": 0,
            "done": 0,
            "failed": 0,
            "last_updated": datetime.datetime.utcnow().isoformat()
        }, indent=2))
    if (d / "lock.json").exists():
        print(f"[init] WARNING: lock.json already present in {d}")
    print(f"[init] Initialized task directory: {d}")

def cmd_status(slug):
    cfg = load_config()
    d = task_dir(cfg, slug)
    if not d.exists():
        print(f"[status] ERROR: task directory not found: {d}")
        sys.exit(1)
    if (d / "lock.json").exists():
        lock = json.loads((d / "lock.json").read_text())
        stale_min = int(cfg.get("LOCK_STALE_MINUTES", 15))
        locked_at = datetime.datetime.fromisoformat(lock.get("locked_at","1970-01-01T00:00:00"))
        age = (datetime.datetime.utcnow() - locked_at).total_seconds() / 60
        if age > stale_min:
            print(f"[status] ERROR: stale lock detected (age={age:.1f}m > {stale_min}m). Run clear-stale-lock first.")
            sys.exit(2)
        else:
            print(f"[status] WARN: active lock (age={age:.1f}m)")
    progress = {}
    if (d / "progress.json").exists():
        progress = json.loads((d / "progress.json").read_text())
    queue_lines = [l for l in (d/"queue.jsonl").read_text().splitlines() if l.strip()]
    done_lines  = [l for l in (d/"done.jsonl").read_text().splitlines() if l.strip()]
    failed_lines= [l for l in (d/"failed.jsonl").read_text().splitlines() if l.strip()]
    print(json.dumps({
        "slug": slug,
        "queued": len(queue_lines),
        "done": len(done_lines),
        "failed": len(failed_lines),
        "progress": progress,
        "batch_size": cfg.get("BATCH_SIZE"),
        "agent_id": cfg.get("AGENT_ID"),
    }, indent=2))

def cmd_clear_stale_lock(slug):
    cfg = load_config()
    d = task_dir(cfg, slug)
    lock_path = d / "lock.json"
    if not lock_path.exists():
        print(f"[clear-stale-lock] No lock file found for {slug}.")
        return
    lock = json.loads(lock_path.read_text())
    stale_min = int(cfg.get("LOCK_STALE_MINUTES", 15))
    locked_at = datetime.datetime.fromisoformat(lock.get("locked_at","1970-01-01T00:00:00"))
    age = (datetime.datetime.utcnow() - locked_at).total_seconds() / 60
    if age > stale_min:
        lock_path.unlink()
        print(f"[clear-stale-lock] Removed stale lock (age={age:.1f}m) for slug '{slug}'.")
    else:
        print(f"[clear-stale-lock] Lock is NOT stale (age={age:.1f}m <= {stale_min}m). Refusing to remove.")
        sys.exit(3)

def cmd_print_supervisor_template():
    tmpl = textwrap.dedent("""\
    #!/usr/bin/env python3
    # AUTO-GENERATED supervisor worker template
    # Fill in SLUG and implement process_item().
    import json, pathlib, datetime

    SLUG = "YOUR_SLUG_HERE"

    def process_item(item: dict) -> bool:
        # TODO: implement
        raise NotImplementedError

    # ... (load config, acquire lock, read queue, process batch, release lock)
    """)
    print(tmpl)

COMMANDS = {
    "init": cmd_init,
    "status": cmd_status,
    "clear-stale-lock": cmd_clear_stale_lock,
    "print-supervisor-template": cmd_print_supervisor_template,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: {sys.argv[0]} <{'|'.join(COMMANDS)}> [slug]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "print-supervisor-template":
        COMMANDS[cmd]()
    else:
        if len(sys.argv) < 3:
            print(f"ERROR: '{cmd}' requires a slug argument.")
            sys.exit(1)
        COMMANDS[cmd](sys.argv[2])
'''

scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(exist_ok=True)
script_path = scripts_dir / "queue_task.py"
script_path.write_text(queue_task_script)
script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# ── Pre-existing stale task directory for slug "compound-screen-2024" ─
# This simulates a crashed previous run that needs recovery
SLUG = "compound-screen-2024"
stale_task_dir = WORKSPACE / "tasks" / SLUG
stale_task_dir.mkdir(parents=True, exist_ok=True)

# Write stale state files (from a previous crashed run)
old_done = [
    {"idempotency_key": f"CMP-{i:04d}", "status": "done", "score": round(random.uniform(0.1, 0.99), 3)}
    for i in range(1, 21)
]
(stale_task_dir / "done.jsonl").write_text(
    "\n".join(json.dumps(r) for r in old_done) + "\n"
)
(stale_task_dir / "failed.jsonl").write_text(
    json.dumps({"idempotency_key": "CMP-0021", "status": "failed", "error": "timeout"}) + "\n"
)
# queue.jsonl is deliberately absent to simulate corruption
# progress.json is stale / wrong counts
(stale_task_dir / "progress.json").write_text(json.dumps({
    "slug": SLUG,
    "total": 50,
    "done": 20,
    "failed": 1,
    "last_updated": "2024-01-15T03:22:11"
}, indent=2))
# stale lock.json — locked 90 minutes ago
stale_lock_time = (
    datetime.datetime.utcnow() - datetime.timedelta(minutes=90)
).replace(microsecond=0).isoformat()
(stale_task_dir / "lock.json").write_text(json.dumps({
    "locked_by": "agent-old-worker",
    "locked_at": stale_lock_time,
    "pid": 99999
}, indent=2))

# ── Raw compound list the agent must enqueue ──────────────────────────
# 30 new compounds not yet in done.jsonl
new_compounds = [
    {"compound_id": f"CMP-{i:04d}", "smiles": f"C{'C'*random.randint(1,5)}O", "priority": random.choice(["high","medium","low"])}
    for i in range(22, 52)
]
(WORKSPACE / "data" / "raw" / "compounds" / "new_batch_2024.json").write_text(
    json.dumps(new_compounds, indent=2)
)

print("Workspace generated successfully.")
print(f"Stale task directory: {stale_task_dir}")
print(f"Stale lock timestamp: {stale_lock_time}")