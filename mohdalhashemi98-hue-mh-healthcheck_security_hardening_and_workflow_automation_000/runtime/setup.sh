#!/bin/bash
set -e

WORKSPACE="/workspace"

# ---- Create the mock `openclaw` CLI ----
cat > /usr/local/bin/openclaw << 'OPENCLAW_SCRIPT'
#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime

STATE_FILE = "/workspace/.openclaw_state.json"

def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def cmd_security_audit(args):
    state = load_state()
    findings = state["audit_results"]["deep"]["findings"]
    
    if "--json" in args:
        print(json.dumps({"findings": findings, "timestamp": datetime.now().isoformat()}, indent=2))
        return
    
    if "--deep" in args:
        print("OpenClaw Deep Security Audit")
        print("=" * 40)
        print(f"Gateway: {state['gateway']['identity']}")
        print(f"Bind: {state['gateway']['bind']}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        for f in findings:
            print(f"[{f['severity']}] {f['issue']}")
            if 'file' in f:
                print(f"       File: {f['file']}")
        print()
        print("Summary: 2 HIGH, 2 MEDIUM, 1 LOW findings")
        print("Run 'openclaw security audit --fix' to apply OpenClaw safe defaults.")
    elif "--fix" in args:
        print("OpenClaw Security Fix")
        print("=" * 40)
        print("Applying OpenClaw safe defaults and tightening file permissions...")
        print("[FIXED] Credentials directory permissions set to 0700")
        print("[FIXED] Log verbosity reduced (request headers excluded)")
        print("[FIXED] Session timeout reduced to 4h")
        print()
        print("NOTE: This does NOT modify host firewall, SSH config, or OS update policies.")
        print("NOTE: These changes affect OpenClaw configuration only.")
    else:
        print("OpenClaw Security Audit (standard)")
        print("=" * 40)
        high = [f for f in findings if f['severity'] == 'HIGH']
        print(f"HIGH findings: {len(high)}")
        for f in high:
            print(f"  - {f['issue']}")
        print("Run with --deep for full report.")

def cmd_update_status(args):
    state = load_state()
    print("OpenClaw Update Status")
    print("=" * 40)
    print(f"Current version : {state['version']}")
    print(f"Latest version  : {state['latest_version']}")
    print(f"Channel         : {state['channel']}")
    if state['update_available']:
        print(f"Status          : UPDATE AVAILABLE (1.8.3 -> 1.9.1)")
    else:
        print(f"Status          : Up to date")

def cmd_status(args):
    state = load_state()
    gw = state['gateway']
    if "--deep" in args:
        print(f"Gateway status  : {gw['status']}")
        print(f"Identity        : {gw['identity']}")
        print(f"Bind address    : {gw['bind']}")
        print(f"Version         : {state['version']}")
    else:
        print(f"OpenClaw gateway: {gw['status']} @ {gw['bind']}")

def cmd_health(args):
    state = load_state()
    if "--json" in args:
        print(json.dumps({"status": "healthy", "gateway": state['gateway']['status'], "version": state['version']}, indent=2))
    else:
        print(f"healthy")

def cmd_cron_list():
    state = load_state()
    jobs = state.get("cron_jobs", [])
    if not jobs:
        print("No cron jobs scheduled.")
        return
    print(f"{'ID':<5} {'NAME':<35} {'SCHEDULE':<20} {'COMMAND'}")
    print("-" * 90)
    for j in jobs:
        print(f"{j['id']:<5} {j['name']:<35} {j['schedule']:<20} {j['command']}")

def cmd_cron_add(args):
    state = load_state()
    # Parse --name, --schedule, --command, --output
    parsed = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--") and i+1 < len(args):
            key = args[i][2:]
            parsed[key] = args[i+1]
            i += 2
        else:
            i += 1
    
    name = parsed.get("name", "")
    schedule = parsed.get("schedule", "")
    command = parsed.get("command", "")
    output = parsed.get("output", "")
    
    # Check for duplicate name
    for j in state["cron_jobs"]:
        if j["name"] == name:
            print(f"ERROR: A cron job with name '{name}' already exists (id={j['id']}). Use 'openclaw cron edit {j['id']}' to update it.")
            sys.exit(1)
    
    new_id = max([j["id"] for j in state["cron_jobs"]], default=0) + 1
    new_job = {
        "id": new_id,
        "name": name,
        "schedule": schedule,
        "command": command,
        "output_location": output,
        "created": datetime.now().isoformat() + "Z"
    }
    state["cron_jobs"].append(new_job)
    save_state(state)
    print(f"Cron job '{name}' added with id={new_id}")
    print(f"Schedule: {schedule}")
    print(f"Command: {command}")
    if output:
        print(f"Output: {output}")
    print()
    print("NOTE: Remember to call 'healthcheck' periodically to review findings and apply fixes.")

def cmd_cron_edit(args):
    state = load_state()
    if not args:
        print("ERROR: cron edit requires a job id")
        sys.exit(1)
    job_id = int(args[0])
    rest = args[1:]
    
    # Parse flags
    parsed = {}
    i = 0
    while i < len(rest):
        if rest[i].startswith("--") and i+1 < len(rest):
            key = rest[i][2:]
            parsed[key] = rest[i+1]
            i += 2
        else:
            i += 1
    
    for j in state["cron_jobs"]:
        if j["id"] == job_id:
            for k, v in parsed.items():
                j[k] = v
            save_state(state)
            print(f"Cron job id={job_id} updated.")
            for k, v in parsed.items():
                print(f"  {k}: {v}")
            print()
            print("NOTE: Remember to call 'healthcheck' periodically to review findings and apply fixes.")
            return
    
    print(f"ERROR: No cron job with id={job_id}")
    sys.exit(1)

def cmd_cron_runs(args):
    print("No run history available.")

def cmd_cron_run(args):
    print("Manually triggered cron run. Check output location for results.")

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: openclaw <command> [args]")
        sys.exit(1)
    
    if args[0] == "security" and len(args) > 1 and args[1] == "audit":
        cmd_security_audit(args[2:])
    elif args[0] == "update" and len(args) > 1 and args[1] == "status":
        cmd_update_status(args[2:])
    elif args[0] == "status":
        cmd_status(args[1:])
    elif args[0] == "health":
        cmd_health(args[1:])
    elif args[0] == "cron":
        if len(args) < 2:
            print("Usage: openclaw cron <list|add|edit|runs|run> [args]")
            sys.exit(1)
        sub = args[1]
        if sub == "list":
            cmd_cron_list()
        elif sub == "add":
            cmd_cron_add(args[2:])
        elif sub == "edit":
            cmd_cron_edit(args[2:])
        elif sub == "runs":
            cmd_cron_runs(args[2:])
        elif sub == "run":
            cmd_cron_run(args[2:])
        else:
            print(f"Unknown cron subcommand: {sub}")
            sys.exit(1)
    else:
        print(f"Unknown command: {' '.join(args)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
OPENCLAW_SCRIPT

chmod +x /usr/local/bin/openclaw

echo "Mock openclaw CLI installed at /usr/local/bin/openclaw"
openclaw status
echo "Setup complete."