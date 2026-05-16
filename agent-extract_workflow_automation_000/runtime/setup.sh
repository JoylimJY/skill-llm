#!/usr/bin/env bash
set -e

HOME_DIR="$HOME"
OPENCLAW_DIR="$HOME_DIR/.openclaw"
BIN_DIR="/usr/local/bin"

# Create the mock `openclaw` CLI that the agent will use
cat > "$BIN_DIR/openclaw" << 'MOCK_OPENCLAW'
#!/usr/bin/env python3
"""
Mock openclaw CLI for sandbox testing.
Supports: cron list, cron add, cron remove, cron run
"""
import sys
import json
import os
import uuid

HOME = os.path.expanduser("~")
CRON_FILE = os.path.join(HOME, ".openclaw", "cron", "jobs.json")

def load_jobs():
    if not os.path.exists(CRON_FILE):
        return {"jobs": []}
    with open(CRON_FILE) as f:
        return json.load(f)

def save_jobs(data):
    with open(CRON_FILE, "w") as f:
        json.dump(data, f, indent=2)

def cmd_cron_list():
    data = load_jobs()
    if not data["jobs"]:
        print("No cron jobs registered.")
        return
    for job in data["jobs"]:
        sched = job.get("schedule", {})
        ms = sched.get("everyMs", "?")
        print(f"  [{job['id']}] {job['name']} | agent={job.get('agentId','?')} | every={ms}ms | sessionTarget={job.get('sessionTarget','?')}")

def cmd_cron_add(args):
    """
    Parse: --name "..." --schedule "every Xm" --agent-id "..." 
           --session-key "..." --session-target "..." 
           --message "..." --delivery "..."
    """
    params = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i+1].startswith("--"):
                params[key] = args[i+1]
                i += 2
            else:
                params[key] = True
                i += 1
        else:
            i += 1

    name = params.get("name", "Unnamed Job")
    schedule_str = params.get("schedule", "every 60m")
    agent_id = params.get("agent-id", "main")
    session_key = params.get("session-key", f"{agent_id}:main")
    session_target = params.get("session-target", "resume")
    message = params.get("message", "")
    delivery = params.get("delivery", "announce")

    # Parse schedule
    every_ms = 1800000  # default 30m
    if "30m" in schedule_str:
        every_ms = 1800000
    elif "60m" in schedule_str or "1h" in schedule_str:
        every_ms = 3600000
    elif "15m" in schedule_str:
        every_ms = 900000
    elif "1m" in schedule_str:
        every_ms = 60000

    job_id = f"job-{str(uuid.uuid4())[:8]}"
    job = {
        "id": job_id,
        "name": name,
        "schedule": {"kind": "every", "everyMs": every_ms},
        "agentId": agent_id,
        "sessionKey": session_key,
        "sessionTarget": session_target,
        "payload": {
            "kind": "agentTurn",
            "message": message
        },
        "delivery": {"mode": delivery}
    }

    data = load_jobs()
    data["jobs"].append(job)
    save_jobs(data)
    print(f"Cron job created: {job_id}")
    print(f"  Name: {name}")
    print(f"  Agent: {agent_id}")
    print(f"  Schedule: every {every_ms}ms")
    print(f"  Session key: {session_key}")
    print(f"  Session target: {session_target}")
    print(f"  Delivery: {delivery}")

def cmd_cron_remove(job_id):
    data = load_jobs()
    before = len(data["jobs"])
    data["jobs"] = [j for j in data["jobs"] if j["id"] != job_id]
    save_jobs(data)
    removed = before - len(data["jobs"])
    print(f"Removed {removed} job(s) with id={job_id}")

def cmd_cron_run(job_id):
    data = load_jobs()
    for job in data["jobs"]:
        if job["id"] == job_id:
            print(f"Manually triggered job {job_id}: {job['name']}")
            return
    print(f"Job {job_id} not found.")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: openclaw <command> [options]")
        sys.exit(0)

    if args[0] == "cron":
        if len(args) < 2:
            print("Usage: openclaw cron <list|add|remove|run> [options]")
            sys.exit(1)
        subcmd = args[1]
        if subcmd == "list":
            cmd_cron_list()
        elif subcmd == "add":
            cmd_cron_add(args[2:])
        elif subcmd == "remove" and len(args) >= 3:
            cmd_cron_remove(args[2])
        elif subcmd == "run" and len(args) >= 3:
            cmd_cron_run(args[2])
        else:
            print(f"Unknown cron subcommand: {subcmd}")
    else:
        print(f"Unknown command: {args[0]}")
MOCK_OPENCLAW

chmod +x "$BIN_DIR/openclaw"

echo "Mock openclaw CLI installed at $BIN_DIR/openclaw"
echo "Verifying..."
openclaw cron list

echo "Setup complete."