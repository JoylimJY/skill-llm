#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"
SKILL_BIN="/usr/local/bin/skill:automation-scripts"

# ── Build the mock `skill:automation-scripts` CLI ────────────────────────────
cat > "$SKILL_BIN" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
Mock implementation of skill:automation-scripts
Faithfully implements all documented behaviours from SKILL.md
"""
import argparse, json, os, sys, time, subprocess, re
from pathlib import Path
from datetime import datetime

SCRIPTS_DIR = Path(os.environ.get("SCRIPTS_DIR", Path.home() / "scripts"))
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
(SCRIPTS_DIR / "templates").mkdir(exist_ok=True)
(SCRIPTS_DIR / "custom").mkdir(exist_ok=True)
(SCRIPTS_DIR / "logs").mkdir(exist_ok=True)

CONFIG_PATH = SCRIPTS_DIR / "config.conf"
SCHEDULE_PATH = SCRIPTS_DIR / ".schedules.json"
STATUS_PATH = SCRIPTS_DIR / ".status.json"

VALID_TYPES = {"monitor", "backup", "sync", "report", "research"}
TYPE_PREFIXES = {
    "monitor": "monitor-",
    "backup": "backup-",
    "sync": "sync-",
    "report": "report-",
    "research": "research-",
}

DEFAULT_CONFIG = {
    "automation": {
        "enabled": True,
        "logRetentionDays": 30,
        "maxRetries": 3,
        "retryDelay": 60,
        "notifications": {
            "onFailure": True,
            "onSuccess": False
        }
    }
}

def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return DEFAULT_CONFIG

def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

def load_schedules():
    if SCHEDULE_PATH.exists():
        try:
            return json.loads(SCHEDULE_PATH.read_text())
        except Exception:
            pass
    return {}

def save_schedules(s):
    SCHEDULE_PATH.write_text(json.dumps(s, indent=2))

def load_status():
    if STATUS_PATH.exists():
        try:
            return json.loads(STATUS_PATH.read_text())
        except Exception:
            pass
    return {}

def save_status(s):
    STATUS_PATH.write_text(json.dumps(s, indent=2))

def get_script_path(name):
    return SCRIPTS_DIR / "custom" / f"{name}.sh"

def cmd_list():
    status = load_status()
    schedules = load_schedules()
    scripts = sorted((SCRIPTS_DIR / "custom").glob("*.sh"))
    if not scripts:
        print("No scripts registered.")
        return
    print(f"{'NAME':<35} {'TYPE':<12} {'STATUS':<10} {'SCHEDULE':<20}")
    print("-" * 80)
    for s in scripts:
        name = s.stem
        stype = "unknown"
        for t, p in TYPE_PREFIXES.items():
            if name.startswith(p):
                stype = t
                break
        st = status.get(name, {})
        enabled = "enabled" if st.get("enabled", True) else "disabled"
        sched = schedules.get(name, {}).get("cron", "-")
        print(f"{name:<35} {stype:<12} {enabled:<10} {sched:<20}")

def cmd_create(name, stype):
    if stype not in VALID_TYPES:
        print(f"ERROR: Invalid type '{stype}'. Must be one of: {', '.join(sorted(VALID_TYPES))}", file=sys.stderr)
        sys.exit(1)
    prefix = TYPE_PREFIXES[stype]
    if not name.startswith(prefix):
        print(f"ERROR: Script name '{name}' must start with '{prefix}' for type '{stype}'", file=sys.stderr)
        sys.exit(1)
    script_path = get_script_path(name)
    if script_path.exists():
        print(f"ERROR: Script '{name}' already exists at {script_path}", file=sys.stderr)
        sys.exit(1)
    template_path = SCRIPTS_DIR / "templates" / f"{stype}.sh"
    if template_path.exists():
        content = template_path.read_text()
        # Replace stub header with proper header
        content = f"#!/bin/bash\n# Auto-generated: {name}\n# Type: {stype}\n# Created: {datetime.now().isoformat()}\n\n" + content
    else:
        content = f"#!/bin/bash\n# Auto-generated: {name}\n# Type: {stype}\n# Created: {datetime.now().isoformat()}\n\necho 'Running {name}'\n"
    script_path.write_text(content)
    script_path.chmod(0o755)
    # Initialise status
    status = load_status()
    status[name] = {"enabled": True, "created": datetime.now().isoformat()}
    save_status(status)
    # Ensure config is canonical
    cfg = load_config()
    if not cfg.get("automation", {}).get("enabled"):
        cfg = DEFAULT_CONFIG
        save_config(cfg)
    print(f"✓ Script '{name}' created successfully at {script_path}")

def cmd_run(name):
    script_path = get_script_path(name)
    if not script_path.exists():
        print(f"ERROR: Script '{name}' not found", file=sys.stderr)
        sys.exit(1)
    status = load_status()
    if not status.get(name, {}).get("enabled", True):
        print(f"ERROR: Script '{name}' is disabled", file=sys.stderr)
        sys.exit(1)
    cfg = load_config()
    max_retries = cfg.get("automation", {}).get("maxRetries", 3)
    retry_delay = cfg.get("automation", {}).get("retryDelay", 60)
    log_path = SCRIPTS_DIR / "logs" / f"{name}.log"
    start = time.time()
    attempt = 0
    result = None
    output_summary = ""
    error_msg = ""
    for attempt in range(max_retries):
        try:
            proc = subprocess.run(
                ["bash", str(script_path)],
                capture_output=True, text=True, timeout=30
            )
            output_summary = (proc.stdout.strip()[:200]) if proc.stdout else ""
            if proc.returncode == 0:
                result = "success"
                break
            else:
                error_msg = proc.stderr.strip()[:200] if proc.stderr else f"exit code {proc.returncode}"
                result = "failure"
        except Exception as e:
            error_msg = str(e)[:200]
            result = "failure"
        if attempt < max_retries - 1:
            time.sleep(0)  # In mock: no actual delay
    duration = round(time.time() - start, 3)
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "script": name,
        "status": result,
        "duration": duration,
        "output": output_summary,
        "error": error_msg if result == "failure" else ""
    }
    # Append to log
    existing = []
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text())
        except Exception:
            existing = []
    existing.append(log_entry)
    log_path.write_text(json.dumps(existing, indent=2))
    icon = "✓" if result == "success" else "✗"
    print(f"{icon} Script '{name}' finished with status: {result} (duration: {duration}s)")
    if result == "failure":
        print(f"  Error: {error_msg}", file=sys.stderr)
        sys.exit(1)

def cmd_log(name):
    log_path = SCRIPTS_DIR / "logs" / f"{name}.log"
    if not log_path.exists():
        print(f"No log found for script '{name}'")
        return
    try:
        entries = json.loads(log_path.read_text())
    except Exception:
        print("Log file is malformed.")
        return
    print(f"Execution log for: {name}")
    print("=" * 60)
    for e in entries:
        print(f"  Timestamp : {e.get('timestamp','')}")
        print(f"  Script    : {e.get('script','')}")
        print(f"  Status    : {e.get('status','')}")
        print(f"  Duration  : {e.get('duration','')}s")
        print(f"  Output    : {e.get('output','')}")
        if e.get("error"):
            print(f"  Error     : {e.get('error','')}")
        print("-" * 40)

def cmd_schedule(name, cron):
    script_path = get_script_path(name)
    if not script_path.exists():
        print(f"ERROR: Script '{name}' not found", file=sys.stderr)
        sys.exit(1)
    # Validate cron expression (5 fields)
    parts = cron.strip().split()
    if len(parts) != 5:
        print(f"ERROR: Invalid cron expression '{cron}'. Must have 5 fields.", file=sys.stderr)
        sys.exit(1)
    schedules = load_schedules()
    schedules[name] = {"cron": cron, "registered": datetime.now().isoformat()}
    save_schedules(schedules)
    print(f"✓ Script '{name}' scheduled with cron: {cron}")

def cmd_disable(name):
    status = load_status()
    if name not in status:
        print(f"ERROR: Script '{name}' not found", file=sys.stderr)
        sys.exit(1)
    status[name]["enabled"] = False
    save_status(status)
    print(f"✓ Script '{name}' disabled")

def cmd_enable(name):
    status = load_status()
    if name not in status:
        print(f"ERROR: Script '{name}' not found", file=sys.stderr)
        sys.exit(1)
    status[name]["enabled"] = True
    save_status(status)
    print(f"✓ Script '{name}' enabled")

def main():
    parser = argparse.ArgumentParser(prog="skill:automation-scripts")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--name", type=str)
    parser.add_argument("--type", type=str)
    parser.add_argument("--run", type=str, metavar="SCRIPT")
    parser.add_argument("--log", type=str, metavar="SCRIPT")
    parser.add_argument("--schedule", type=str, metavar="SCRIPT")
    parser.add_argument("--cron", type=str)
    parser.add_argument("--disable", type=str, metavar="SCRIPT")
    parser.add_argument("--enable", type=str, metavar="SCRIPT")
    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.create:
        if not args.name or not args.type:
            print("ERROR: --create requires --name and --type", file=sys.stderr)
            sys.exit(1)
        cmd_create(args.name, args.type)
    elif args.run:
        cmd_run(args.run)
    elif args.log:
        cmd_log(args.log)
    elif args.schedule:
        if not args.cron:
            print("ERROR: --schedule requires --cron", file=sys.stderr)
            sys.exit(1)
        cmd_schedule(args.schedule, args.cron)
    elif args.disable:
        cmd_disable(args.disable)
    elif args.enable:
        cmd_enable(args.enable)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
PYTHON_SCRIPT

chmod +x "$SKILL_BIN"

# Point SCRIPTS_DIR to the workspace/scripts dir
export SCRIPTS_DIR="/workspace/scripts"
echo "export SCRIPTS_DIR=/workspace/scripts" >> /etc/bash.bashrc
echo "export SCRIPTS_DIR=/workspace/scripts" >> /etc/environment

# Ensure the mock can find SCRIPTS_DIR at runtime via env
sed -i "1a import os; os.environ.setdefault('SCRIPTS_DIR', '/workspace/scripts')" "$SKILL_BIN"

echo "Mock skill:automation-scripts installed at $SKILL_BIN"
echo "SCRIPTS_DIR=/workspace/scripts"