import os
import yaml
import json
import random
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

HOME = Path("/home/agent")

# ── Core OpenClaw directory structure ──────────────────────────────────────────
openclaw_base = HOME / ".openclaw"
task_router_base = openclaw_base / "task-router"

dirs = [
    task_router_base / "queue" / "pending",
    task_router_base / "queue" / "active",
    task_router_base / "queue" / "completed",
    task_router_base / "queue" / "failed",
    task_router_base / "dead-letter",
    task_router_base / "logs",
    openclaw_base / "workspace",
    openclaw_base / "sessions",
    openclaw_base / "agents" / "genome-sequencer" / "memory",
    openclaw_base / "agents" / "variant-caller" / "memory",
    openclaw_base / "agents" / "annotator" / "memory",
    openclaw_base / "agents" / "report-gen" / "memory",
    HOME / "projects" / "genomics-pipeline" / "inputs",
    HOME / "projects" / "genomics-pipeline" / "outputs",
    HOME / "projects" / "genomics-pipeline" / "scripts",
    HOME / "projects" / "admin" / "logs",
    HOME / "projects" / "admin" / "configs",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ── Intentionally BROKEN config.yaml (wrong strategy names, missing sections) ──
broken_config = {
    "router": {
        "check_interval": 30,
        "default_ttl": 3600,
        "max_retries": 2,
        "strategies": {
            # Wrong: uses invalid strategy names and missing by_type entries
            "default": "random-pick",
            "by_type": {
                "sequencing": "overload-first",
                "variant_calling": "round-robin",
                # Missing: alignment, annotation strategies
            }
        },
        "health": {
            "agent_timeout": 300,
            "task_timeout": {
                "warning": 1800,
                "critical": 3600
            }
        },
        "notifications": {
            "on_complete": True,
            "on_fail": True,
            "channels": ["main_session"]
        }
    }
}
with open(task_router_base / "config.yaml", "w") as f:
    yaml.dump(broken_config, f, default_flow_style=False)

# ── Intentionally EMPTY agents.yaml (no agents registered yet) ────────────────
agents_yaml = {"agents": {}}
with open(task_router_base / "agents.yaml", "w") as f:
    yaml.dump(agents_yaml, f, default_flow_style=False)

# ── A DEAD-LETTER task that must be retried ────────────────────────────────────
dead_task_id = "task-dl-9f3a2b"
dead_task = {
    "id": dead_task_id,
    "type": "variant_calling",
    "title": "Call variants on sample GS-0042",
    "description": "Identify SNPs and indels from aligned BAM file for patient sample GS-0042",
    "payload": {
        "sample_id": "GS-0042",
        "bam_file": "/data/aligned/GS-0042.bam",
        "reference": "hg38",
        "output_format": "vcf"
    },
    "created_by": "main",
    "assigned_to": "variant-caller-v1",
    "assigned_by": "router",
    "created_at": "2026-01-10T08:00:00Z",
    "assigned_at": "2026-01-10T08:05:00Z",
    "started_at": "2026-01-10T08:06:00Z",
    "completed_at": None,
    "expires_at": "2026-01-10T09:00:00Z",
    "priority": "high",
    "ttl": 3600,
    "retries": 2,
    "max_retries": 2,
    "dependencies": [],
    "blocked_by": [],
    "status": "dead_letter",
    "result": None,
    "error": "Segmentation fault in GATK HaplotypeCaller: reference index corrupted",
    "metadata": {
        "source": "heartbeat",
        "tags": ["GS-0042", "variant-calling", "hg38"]
    }
}
with open(task_router_base / "dead-letter" / f"{dead_task_id}.yaml", "w") as f:
    yaml.dump(dead_task, f, default_flow_style=False)

# Dead-letter index
dead_letter_index = {
    "dead_letters": [
        {
            "id": dead_task_id,
            "title": "Call variants on sample GS-0042",
            "type": "variant_calling",
            "error": "Segmentation fault in GATK HaplotypeCaller: reference index corrupted",
            "timestamp": "2026-01-10T09:00:00Z"
        }
    ]
}
with open(task_router_base / "dead-letter" / "index.yaml", "w") as f:
    yaml.dump(dead_letter_index, f, default_flow_style=False)

# ── Some completed tasks (distractor) ─────────────────────────────────────────
for i, sample in enumerate(["GS-0001", "GS-0002", "GS-0003"]):
    t_id = f"task-comp-{i:04d}"
    completed_task = {
        "id": t_id,
        "type": "sequencing",
        "title": f"Sequence sample {sample}",
        "status": "complete",
        "created_by": "main",
        "assigned_to": "seq-agent-1",
        "priority": "normal",
        "result": f"/data/results/{sample}_seq.fastq",
        "retries": 0,
        "max_retries": 2,
        "dependencies": [],
        "error": None
    }
    with open(task_router_base / "queue" / "completed" / f"{t_id}.yaml", "w") as f:
        yaml.dump(completed_task, f, default_flow_style=False)

# ── Router log (distractor with misleading old entries) ───────────────────────
log_lines = [
    "2026-01-09T10:00:00Z [INFO] Router cycle: 0 pending tasks",
    "2026-01-09T10:05:00Z [WARN] No healthy agents available",
    "2026-01-09T10:30:00Z [INFO] Routed task-comp-0000 → seq-agent-1",
    "2026-01-10T08:05:00Z [INFO] Routed task-dl-9f3a2b → variant-caller-v1",
    "2026-01-10T09:00:00Z [ERROR] task-dl-9f3a2b: retries=2 exhausted, moving to dead-letter",
]
with open(task_router_base / "logs" / "router.log", "w") as f:
    f.write("\n".join(log_lines) + "\n")

# ── Distractor files in project directories ───────────────────────────────────
distractors = [
    (HOME / "projects" / "genomics-pipeline" / "scripts" / "preprocess.sh",
     "#!/bin/bash\n# Preprocessing pipeline\nbwa mem hg38 sample.fastq > aligned.sam\n"),
    (HOME / "projects" / "genomics-pipeline" / "scripts" / "variant_call.sh",
     "#!/bin/bash\n# Variant calling\ngatk HaplotypeCaller -R hg38.fa -I aligned.bam -O output.vcf\n"),
    (HOME / "projects" / "genomics-pipeline" / "inputs" / "samples.tsv",
     "sample_id\tpatient\tstatus\nGS-0042\tP-1042\tpending\nGS-0043\tP-1043\tqueued\n"),
    (HOME / "projects" / "genomics-pipeline" / "outputs" / "pipeline_run_20260110.log",
     "Pipeline started: 2026-01-10T08:00:00Z\nStep 1: FASTQ QC - PASSED\nStep 2: Alignment - PASSED\nStep 3: Variant calling - FAILED\n"),
    (HOME / "projects" / "admin" / "logs" / "system.log",
     "2026-01-10T07:00:00Z kernel: system boot\n2026-01-10T07:01:00Z sshd: started\n"),
    (HOME / "projects" / "admin" / "configs" / "pipeline.conf",
     "[pipeline]\nreference=hg38\nthreads=8\nmemory=32G\n"),
    (HOME / ".openclaw" / "workspace" / "NOTES.md",
     "# Pipeline Notes\n- GS-0042 variant calling failed on Jan 10\n- Need to re-run with fresh reference index\n- Contact bioinformatics team for hg38 index rebuild\n"),
    (HOME / ".openclaw" / "sessions" / "session-001.yaml",
     "id: session-001\nstarted: 2026-01-10T07:55:00Z\nagent: main\nstatus: idle\n"),
    (HOME / ".openclaw" / "agents" / "genome-sequencer" / "memory" / "last_run.txt",
     "Last sequencing run: GS-0003\nCompleted: 2026-01-09T23:45:00Z\nOutput: /data/results/GS-0003_seq.fastq\n"),
    (HOME / ".openclaw" / "agents" / "report-gen" / "memory" / "templates.yaml",
     "templates:\n  - variant_report\n  - alignment_summary\n  - qc_metrics\n"),
]
for path, content in distractors:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

# ── Mock `task` CLI shim (simulates the real task-router CLI) ─────────────────
# This is what the setup_script will make executable.
mock_task_cli = HOME / ".local" / "bin" / "task"
mock_task_cli.parent.mkdir(parents=True, exist_ok=True)

cli_script = r'''#!/usr/bin/env python3
"""
Mock task-router CLI for evaluation environment.
Implements the subset of commands needed for the benchmark task.
State is persisted to ~/.openclaw/task-router/
"""
import sys, os, yaml, json, uuid, argparse
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.home() / ".openclaw" / "task-router"
AGENTS_FILE = BASE / "agents.yaml"
CONFIG_FILE = BASE / "config.yaml"
QUEUE = BASE / "queue"
DEAD_LETTER = BASE / "dead-letter"

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def load_agents():
    if not AGENTS_FILE.exists():
        return {"agents": {}}
    with open(AGENTS_FILE) as f:
        return yaml.safe_load(f) or {"agents": {}}

def save_agents(data):
    with open(AGENTS_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False)

def load_config():
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f) or {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False)

def gen_task_id():
    return "task-" + str(uuid.uuid4())[:8]

def find_task(task_id):
    for subdir in ["pending", "active", "completed", "failed"]:
        p = QUEUE / subdir / f"{task_id}.yaml"
        if p.exists():
            return p, subdir
    return None, None

def load_task(task_id):
    path, folder = find_task(task_id)
    if path:
        with open(path) as f:
            return yaml.safe_load(f), path, folder
    return None, None, None

def save_task(task, path):
    with open(path, "w") as f:
        yaml.dump(task, f, default_flow_style=False)

def cmd_agent(args):
    sub = args[0] if args else ""
    if sub == "register":
        p = argparse.ArgumentParser()
        p.add_argument("name")
        p.add_argument("--capabilities", required=True)
        p.add_argument("--max-concurrent", type=int, default=2)
        p.add_argument("--emoji", default="🤖")
        opts = p.parse_args(args[1:])
        caps = opts.capabilities.split()
        data = load_agents()
        data["agents"][opts.name] = {
            "id": opts.name,
            "emoji": opts.emoji,
            "capabilities": caps,
            "max_concurrent": opts.max_concurrent,
            "current_tasks": [],
            "stats": {"completed": 0, "failed": 0, "avg_duration": 0},
            "health": {"last_ping": now_iso(), "status": "healthy"}
        }
        save_agents(data)
        print(f"Agent '{opts.name}' registered with capabilities: {caps}")

    elif sub == "list":
        data = load_agents()
        if not data["agents"]:
            print("No agents registered.")
            return
        p = argparse.ArgumentParser()
        p.add_argument("--capable-of", default=None)
        opts = p.parse_args(args[1:])
        for name, agent in data["agents"].items():
            if opts.capable_of and opts.capable_of not in agent.get("capabilities", []):
                continue
            caps = ", ".join(agent.get("capabilities", []))
            print(f"{agent.get('emoji','🤖')} {name}: capabilities=[{caps}] max_concurrent={agent.get('max_concurrent',2)} status={agent['health']['status']}")

    elif sub == "status":
        if len(args) < 2:
            print("Usage: task agent status <name>"); return
        agent_name = args[1]
        data = load_agents()
        if agent_name not in data["agents"]:
            print(f"Agent '{agent_name}' not found."); return
        agent = data["agents"][agent_name]
        print(yaml.dump(agent))

    elif sub == "update":
        if len(args) < 2:
            print("Usage: task agent update <name> [options]"); return
        agent_name = args[1]
        p = argparse.ArgumentParser()
        p.add_argument("--add-capability", default=None)
        p.add_argument("--max-concurrent", type=int, default=None)
        opts = p.parse_args(args[2:])
        data = load_agents()
        if agent_name not in data["agents"]:
            print(f"Agent '{agent_name}' not found."); return
        if opts.add_capability:
            caps = data["agents"][agent_name].get("capabilities", [])
            if opts.add_capability not in caps:
                caps.append(opts.add_capability)
            data["agents"][agent_name]["capabilities"] = caps
        if opts.max_concurrent is not None:
            data["agents"][agent_name]["max_concurrent"] = opts.max_concurrent
        save_agents(data)
        print(f"Agent '{agent_name}' updated.")

    elif sub == "unregister":
        if len(args) < 2:
            print("Usage: task agent unregister <name>"); return
        agent_name = args[1]
        p = argparse.ArgumentParser()
        p.add_argument("--reassign-tasks", action="store_true")
        opts = p.parse_args(args[2:])
        data = load_agents()
        if agent_name in data["agents"]:
            del data["agents"][agent_name]
            save_agents(data)
        print(f"Agent '{agent_name}' unregistered.")

    else:
        print(f"Unknown agent subcommand: {sub}")

def cmd_create(args):
    p = argparse.ArgumentParser()
    p.add_argument("--type", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--data", default="{}")
    p.add_argument("--priority", default="normal")
    p.add_argument("--ttl", type=int, default=3600)
    p.add_argument("--depends-on", default=None)
    p.add_argument("--created-by", default="main")
    p.add_argument("--max-retries", type=int, default=2)
    opts = p.parse_args(args)

    try:
        payload = json.loads(opts.data)
    except json.JSONDecodeError:
        payload = {}

    task_id = gen_task_id()
    deps = [opts.depends_on] if opts.depends_on else []

    task = {
        "id": task_id,
        "type": opts.type,
        "title": opts.title,
        "description": opts.description,
        "payload": payload,
        "created_by": opts.created_by,
        "assigned_to": None,
        "assigned_by": None,
        "created_at": now_iso(),
        "assigned_at": None,
        "started_at": None,
        "completed_at": None,
        "expires_at": None,
        "priority": opts.priority,
        "ttl": opts.ttl,
        "retries": 0,
        "max_retries": opts.max_retries,
        "dependencies": deps,
        "blocked_by": [],
        "status": "pending",
        "result": None,
        "error": None,
        "metadata": {"source": "cli", "tags": []}
    }

    out_path = QUEUE / "pending" / f"{task_id}.yaml"
    with open(out_path, "w") as f:
        yaml.dump(task, f, default_flow_style=False)

    print(f"Created task: {task_id}")
    print(f"  Title: {opts.title}")
    print(f"  Type: {opts.type}")
    print(f"  Priority: {opts.priority}")
    if deps:
        print(f"  Dependencies: {deps}")
    return task_id

def cmd_list(args):
    p = argparse.ArgumentParser()
    p.add_argument("--status", default=None)
    p.add_argument("--assigned-to", default=None)
    p.add_argument("--type", default=None)
    p.add_argument("--limit", type=int, default=100)
    opts = p.parse_args(args)

    results = []
    folders = ["pending", "active", "completed", "failed"] if not opts.status else [opts.status]
    for folder in folders:
        folder_path = QUEUE / folder
        if not folder_path.exists():
            continue
        for f in folder_path.glob("*.yaml"):
            with open(f) as fh:
                t = yaml.safe_load(fh)
            if opts.assigned_to and t.get("assigned_to") != opts.assigned_to:
                continue
            if opts.type and t.get("type") != opts.type:
                continue
            results.append(t)

    for t in results[:opts.limit]:
        print(f"{t['id']} [{t['status']}] {t['title']} (type={t['type']}, priority={t.get('priority','normal')})")

def cmd_show(args):
    if not args:
        print("Usage: task show <task_id>"); return
    task_id = args[0]
    task, path, folder = load_task(task_id)
    if not task:
        # Check dead-letter
        dl_path = DEAD_LETTER / f"{task_id}.yaml"
        if dl_path.exists():
            with open(dl_path) as f:
                task = yaml.safe_load(f)
            print(yaml.dump(task))
        else:
            print(f"Task '{task_id}' not found.")
        return
    print(yaml.dump(task))

def cmd_cancel(args):
    if not args:
        print("Usage: task cancel <task_id>"); return
    task_id = args[0]
    task, path, folder = load_task(task_id)
    if not task:
        print(f"Task '{task_id}' not found."); return
    if folder in ("completed", "failed"):
        print(f"Cannot cancel task in '{folder}' state."); return
    task["status"] = "failed"
    task["error"] = "Cancelled by user"
    new_path = QUEUE / "failed" / f"{task_id}.yaml"
    path.unlink()
    save_task(task, new_path)
    print(f"Task '{task_id}' cancelled.")

def cmd_retry(args):
    if not args:
        print("Usage: task retry <task_id>"); return
    task_id = args[0]
    task, path, folder = load_task(task_id)
    if not task:
        print(f"Task '{task_id}' not found in queue."); return
    task["status"] = "pending"
    task["retries"] = task.get("retries", 0) + 1
    task["assigned_to"] = None
    task["assigned_at"] = None
    task["started_at"] = None
    task["error"] = None
    new_path = QUEUE / "pending" / f"{task_id}.yaml"
    path.unlink()
    save_task(task, new_path)
    print(f"Task '{task_id}' moved back to pending (retry #{task['retries']}).")

def cmd_reprioritize(args):
    if not args:
        print("Usage: task reprioritize <task_id> --priority <p>"); return
    task_id = args[0]
    p = argparse.ArgumentParser()
    p.add_argument("--priority", required=True)
    opts = p.parse_args(args[1:])
    task, path, folder = load_task(task_id)
    if not task:
        print(f"Task '{task_id}' not found."); return
    task["priority"] = opts.priority
    save_task(task, path)
    print(f"Task '{task_id}' priority updated to '{opts.priority}'.")

def cmd_dead_letter(args):
    sub = args[0] if args else ""
    if sub == "list":
        index_path = DEAD_LETTER / "index.yaml"
        if not index_path.exists():
            print("No dead-letter tasks."); return
        with open(index_path) as f:
            index = yaml.safe_load(f)
        for item in index.get("dead_letters", []):
            print(f"{item['id']}: {item['title']} | error: {item.get('error','?')}")

    elif sub == "show":
        if len(args) < 2:
            print("Usage: task dead-letter show <id>"); return
        dl_id = args[1]
        dl_path = DEAD_LETTER / f"{dl_id}.yaml"
        if not dl_path.exists():
            print(f"Dead-letter task '{dl_id}' not found."); return
        with open(dl_path) as f:
            task = yaml.safe_load(f)
        print(yaml.dump(task))

    elif sub == "retry":
        if len(args) < 2:
            print("Usage: task dead-letter retry <id>"); return
        dl_id = args[1]
        dl_path = DEAD_LETTER / f"{dl_id}.yaml"
        if not dl_path.exists():
            print(f"Dead-letter task '{dl_id}' not found."); return
        with open(dl_path) as f:
            task = yaml.safe_load(f)
        # Reset and move to pending
        task["status"] = "pending"
        task["retries"] = 0
        task["assigned_to"] = None
        task["assigned_at"] = None
        task["started_at"] = None
        task["error"] = None
        pending_path = QUEUE / "pending" / f"{dl_id}.yaml"
        with open(pending_path, "w") as f:
            yaml.dump(task, f, default_flow_style=False)
        dl_path.unlink()
        # Update index
        index_path = DEAD_LETTER / "index.yaml"
        if index_path.exists():
            with open(index_path) as f:
                index = yaml.safe_load(f) or {"dead_letters": []}
            index["dead_letters"] = [x for x in index.get("dead_letters", []) if x["id"] != dl_id]
            with open(index_path, "w") as f:
                yaml.dump(index, f, default_flow_style=False)
        print(f"Dead-letter task '{dl_id}' moved to pending queue for retry.")

    elif sub == "reassign":
        if len(args) < 2:
            print("Usage: task dead-letter reassign <id> --to <agent>"); return
        dl_id = args[1]
        p = argparse.ArgumentParser()
        p.add_argument("--to", required=True)
        opts = p.parse_args(args[2:])
        dl_path = DEAD_LETTER / f"{dl_id}.yaml"
        if not dl_path.exists():
            print(f"Dead-letter task '{dl_id}' not found."); return
        with open(dl_path) as f:
            task = yaml.safe_load(f)
        task["status"] = "assigned"
        task["assigned_to"] = opts.to
        task["assigned_by"] = "manual"
        task["assigned_at"] = now_iso()
        task["retries"] = 0
        task["error"] = None
        active_path = QUEUE / "active" / f"{dl_id}.yaml"
        with open(active_path, "w") as f:
            yaml.dump(task, f, default_flow_style=False)
        dl_path.unlink()
        print(f"Dead-letter task '{dl_id}' reassigned to '{opts.to}'.")

    elif sub == "archive":
        if len(args) < 2:
            print("Usage: task dead-letter archive <id>"); return
        dl_id = args[1]
        dl_path = DEAD_LETTER / f"{dl_id}.yaml"
        if dl_path.exists():
            dl_path.unlink()
        print(f"Dead-letter task '{dl_id}' archived.")

    else:
        print(f"Unknown dead-letter subcommand: {sub}")

def cmd_router(args):
    sub = args[0] if args else ""
    if sub == "status":
        pending = list((QUEUE / "pending").glob("*.yaml"))
        active = list((QUEUE / "active").glob("*.yaml"))
        data = load_agents()
        healthy = [a for a in data["agents"].values() if a["health"]["status"] == "healthy"]
        print(f"Router status:")
        print(f"  Pending tasks: {len(pending)}")
        print(f"  Active tasks: {len(active)}")
        print(f"  Healthy agents: {len(healthy)}")
    elif sub in ("pause", "resume", "rebalance", "cleanup", "drain"):
        print(f"Router {sub}: OK")
    else:
        print(f"Unknown router subcommand: {sub}")

def cmd_result(args):
    if not args:
        print("Usage: task result <task_id>"); return
    task_id = args[0]
    task, path, folder = load_task(task_id)
    if not task:
        print(f"Task '{task_id}' not found."); return
    if task.get("result"):
        print(f"Result: {task['result']}")
    else:
        print(f"No result available for task '{task_id}'.")

def main():
    if len(sys.argv) < 2:
        print("Usage: task <command> [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    rest = sys.argv[2:]

    if cmd == "agent":
        cmd_agent(rest)
    elif cmd == "create":
        cmd_create(rest)
    elif cmd == "list":
        cmd_list(rest)
    elif cmd == "show":
        cmd_show(rest)
    elif cmd == "cancel":
        cmd_cancel(rest)
    elif cmd == "retry":
        cmd_retry(rest)
    elif cmd == "reprioritize":
        cmd_reprioritize(rest)
    elif cmd == "dead-letter":
        cmd_dead_letter(rest)
    elif cmd == "router":
        cmd_router(rest)
    elif cmd == "result":
        cmd_result(rest)
    elif cmd == "export":
        print("Export: not implemented in mock")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

mock_task_cli.write_text(cli_script)
mock_task_cli.chmod(0o755)

print("Workspace generated successfully.")
print(f"  Task router base: {task_router_base}")
print(f"  Dead-letter task: {dead_task_id}")
print(f"  Mock CLI: {mock_task_cli}")