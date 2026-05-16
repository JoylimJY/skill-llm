#!/bin/bash
set -e

# Create agpair state directory
mkdir -p /tmp/agpair_state
chmod 777 /tmp/agpair_state

# Write the mock agpair CLI
cat > /usr/local/bin/agpair << 'AGPAIR_EOF'
#!/usr/bin/env python3
"""
Mock agpair CLI — simulates the Antigravity pair-programming control surface.
Records all invocations to /tmp/agpair_state/invocations.log for eval.
Maintains stateful task lifecycle in /tmp/agpair_state/.
"""
import sys
import json
import os
import time
import uuid
from pathlib import Path
from datetime import datetime

STATE_DIR = Path("/tmp/agpair_state")
STATE_DIR.mkdir(exist_ok=True)
INVOCATIONS_LOG = STATE_DIR / "invocations.log"
TASK_STATE_FILE = STATE_DIR / "task_state.json"
ACTIVE_TASK_FILE = STATE_DIR / "active_task_id.txt"

def log_invocation(cmd_args):
    """Record every invocation with timestamp."""
    with open(INVOCATIONS_LOG, "a") as f:
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "args": cmd_args
        }
        f.write(json.dumps(entry) + "\n")

def get_task_state():
    if TASK_STATE_FILE.exists():
        return json.loads(TASK_STATE_FILE.read_text())
    return None

def save_task_state(state):
    TASK_STATE_FILE.write_text(json.dumps(state, indent=2))

def get_call_count():
    """Count how many times agpair has been invoked total."""
    if not INVOCATIONS_LOG.exists():
        return 0
    return sum(1 for line in INVOCATIONS_LOG.read_text().splitlines() if line.strip())

def cmd_doctor(args):
    repo_path = None
    for i, a in enumerate(args):
        if a == "--repo-path" and i + 1 < len(args):
            repo_path = args[i + 1]
    
    if not repo_path:
        print("ERROR: --repo-path is required")
        sys.exit(1)
    
    resolved = Path(repo_path).resolve()
    exists = resolved.exists()
    
    print(f"agpair doctor report")
    print(f"  repo_path           : {repo_path}")
    print(f"  resolved_path       : {resolved}")
    print(f"  path_exists         : {exists}")
    print(f"  desktop_reader_conflict : false")
    print(f"  repo_bridge_session_ready : true")
    print(f"  git_repo_detected   : {(resolved / '.git').exists() or exists}")
    print(f"  status              : HEALTHY")

def cmd_daemon(args):
    if not args:
        print("Usage: agpair daemon <status|start|stop>")
        sys.exit(1)
    sub = args[0]
    if sub == "status":
        print("agpair daemon status")
        print("  running     : true")
        print("  pid         : 12345")
        print("  uptime      : 4h 22m")
        print("  transport   : unix_socket")
        print("  status      : OK")
    elif sub == "start":
        print("daemon already running (pid 12345)")
    else:
        print(f"unknown daemon subcommand: {sub}")
        sys.exit(1)

def cmd_task(args):
    if not args:
        print("Usage: agpair task <start|status|logs|wait|active-waits> ...")
        sys.exit(1)
    sub = args[0]
    rest = args[1:]

    if sub == "start":
        return cmd_task_start(rest)
    elif sub == "status":
        return cmd_task_status(rest)
    elif sub == "logs":
        return cmd_task_logs(rest)
    elif sub == "wait":
        return cmd_task_wait(rest)
    elif sub == "active-waits":
        return cmd_task_active_waits(rest)
    else:
        print(f"unknown task subcommand: {sub}")
        sys.exit(1)

def cmd_task_start(args):
    description = None
    repo_path = None
    no_wait = False
    i = 0
    while i < len(args):
        if args[i] == "--repo-path" and i+1 < len(args):
            repo_path = args[i+1]; i += 2
        elif args[i] == "--no-wait":
            no_wait = True; i += 1
        elif not args[i].startswith("--"):
            description = args[i]; i += 1
        else:
            i += 1
    
    task_id = "TASK-" + str(uuid.uuid4())[:8].upper()
    ACTIVE_TASK_FILE.write_text(task_id)
    
    # Save initial state — task is "running"
    state = {
        "task_id": task_id,
        "status": "running",
        "waiter_state": "waiting",
        "phase": "executing",
        "repo_path": repo_path or "",
        "description": description or "",
        "created_at": datetime.utcnow().isoformat(),
        "status_poll_count": 0,
        "active_waits_poll_count": 0,
        "semantic_action": None
    }
    save_task_state(state)
    
    print(f"Task dispatched.")
    print(f"  task_id  : {task_id}")
    print(f"  status   : ACK")
    print(f"  message  : Task accepted by Antigravity backend. Processing has begun.")
    print(f"")
    print(f"NOTE: ACK means the task was accepted, not completed.")
    print(f"Use 'agpair task status {task_id}' or 'agpair task active-waits' to monitor progress.")

def cmd_task_status(args):
    task_id = args[0] if args else None
    if not task_id:
        if ACTIVE_TASK_FILE.exists():
            task_id = ACTIVE_TASK_FILE.read_text().strip()
        else:
            print("ERROR: task_id required")
            sys.exit(1)
    
    state = get_task_state()
    if not state or state["task_id"] != task_id:
        print(f"ERROR: task {task_id} not found")
        sys.exit(1)
    
    # Advance state: first 2 polls → running/waiting, after → EVIDENCE_PACK
    poll_count = state.get("status_poll_count", 0)
    state["status_poll_count"] = poll_count + 1
    
    if poll_count < 2:
        status = "running"
        waiter_state = "waiting"
        phase = "executing"
    else:
        status = "EVIDENCE_PACK"
        waiter_state = "terminal"
        phase = "complete"
        state["status"] = status
        state["waiter_state"] = waiter_state
    
    save_task_state(state)
    
    print(f"Task Status: {task_id}")
    print(f"  status       : {status}")
    print(f"  waiter_state : {waiter_state}")
    print(f"  phase        : {phase}")
    print(f"  repo_path    : {state.get('repo_path', '')}")
    if status == "EVIDENCE_PACK":
        print(f"  evidence     : Refactoring complete. 47 lines changed across 1 file.")
        print(f"  commits      : 1 pending commit awaiting approval")

def cmd_task_active_waits(args):
    state = get_task_state()
    if not state:
        print("active-waits: []")
        return
    
    task_id = state["task_id"]
    aw_count = state.get("active_waits_poll_count", 0)
    state["active_waits_poll_count"] = aw_count + 1
    save_task_state(state)
    
    # First 2 checks show active wait; after that, cleared
    if aw_count < 2 and state.get("waiter_state") != "terminal":
        print(f"active-waits:")
        print(f"  - task_id     : {task_id}")
        print(f"    waiter_state: waiting")
        print(f"    started_at  : {state.get('created_at','')}")
    else:
        print("active-waits: []")
        print("(no active waiters — task has reached terminal state)")

def cmd_task_logs(args):
    task_id = None
    limit = 20
    i = 0
    while i < len(args):
        if args[i] == "--limit" and i+1 < len(args):
            limit = int(args[i+1]); i += 2
        elif not args[i].startswith("--"):
            task_id = args[i]; i += 1
        else:
            i += 1
    
    if not task_id:
        if ACTIVE_TASK_FILE.exists():
            task_id = ACTIVE_TASK_FILE.read_text().strip()
        else:
            print("ERROR: task_id required"); sys.exit(1)
    
    state = get_task_state()
    logs_available = state and state.get("status_poll_count", 0) >= 2

    print(f"Logs for task {task_id} (--limit {limit}):")
    print(f"  [INFO ] 2024-01-15T14:00:01Z  Task started: refactor PaymentProcessor")
    print(f"  [INFO ] 2024-01-15T14:00:02Z  Parsing repo: payments_service/src/core/processor.py")
    print(f"  [INFO ] 2024-01-15T14:00:03Z  Identified 4 refactoring targets")
    print(f"  [INFO ] 2024-01-15T14:00:05Z  Replacing MD5 transaction IDs with uuid.uuid4()")
    print(f"  [INFO ] 2024-01-15T14:00:07Z  Adding idempotency_key parameter to process()")
    print(f"  [INFO ] 2024-01-15T14:00:09Z  Refactoring __init__ to accept db parameter")
    print(f"  [INFO ] 2024-01-15T14:00:11Z  Integrating validate_account() from utils.validation")
    print(f"  [INFO ] 2024-01-15T14:00:13Z  Running unit tests: 2/2 passed")
    print(f"  [INFO ] 2024-01-15T14:00:14Z  Generating EVIDENCE_PACK")
    print(f"  [INFO ] 2024-01-15T14:00:15Z  Refactoring complete. All acceptance criteria met.")
    print(f"  [INFO ] 2024-01-15T14:00:15Z  Status: EVIDENCE_PACK — awaiting reviewer approval")
    
    # Record whether --limit was used
    state_update = get_task_state()
    if state_update:
        state_update["logs_limit_used"] = limit
        save_task_state(state_update)

def cmd_task_wait(args):
    task_id = args[0] if args else None
    if not task_id and ACTIVE_TASK_FILE.exists():
        task_id = ACTIVE_TASK_FILE.read_text().strip()
    
    print(f"Waiting for task {task_id} to reach terminal state...")
    print(f"  (poll 1) status: running  waiter_state: waiting")
    print(f"  (poll 2) status: running  waiter_state: waiting")
    print(f"  (poll 3) status: EVIDENCE_PACK  waiter_state: terminal")
    print(f"Wait complete. Task reached terminal state: EVIDENCE_PACK")
    
    state = get_task_state()
    if state:
        state["status"] = "EVIDENCE_PACK"
        state["waiter_state"] = "terminal"
        state["status_poll_count"] = 3
        save_task_state(state)

def cmd_semantic(action, args):
    task_id = args[0] if args else None
    force = "--force" in args
    
    if not task_id:
        if ACTIVE_TASK_FILE.exists():
            task_id = ACTIVE_TASK_FILE.read_text().strip()
        else:
            print("ERROR: task_id required"); sys.exit(1)
    
    state = get_task_state()
    if not state or state["task_id"] != task_id:
        print(f"ERROR: task {task_id} not found"); sys.exit(1)
    
    # Guard: refuse semantic action if active waiter still exists
    aw_count = state.get("active_waits_poll_count", 0)
    waiter_state = state.get("waiter_state", "waiting")
    
    if waiter_state == "waiting" and not force:
        print(f"ERROR: Cannot send '{action}' — task {task_id} has an active waiter.")
        print(f"  waiter_state : waiting")
        print(f"  Use 'agpair task active-waits' to check, or --force if waiter is orphaned.")
        sys.exit(1)
    
    state["semantic_action"] = action
    state["status"] = "COMMITTED" if action == "approve" else f"post_{action}"
    save_task_state(state)
    
    if action == "approve":
        print(f"Task {task_id}: APPROVED")
        print(f"  status  : COMMITTED")
        print(f"  message : Changes have been committed to the repository.")
        print(f"  commit  : abc123f  refactor: PaymentProcessor idempotency + DI")
    elif action == "reject":
        print(f"Task {task_id}: REJECTED")
        print(f"  status  : rejected")
        print(f"  message : Rejection noted. Session remains open for continuation.")
    elif action == "continue":
        print(f"Task {task_id}: CONTINUE sent")
        print(f"  status  : continued")
    elif action == "retry":
        print(f"Task {task_id}: RETRY initiated")
        print(f"  status  : retrying")

def main():
    args = sys.argv[1:]
    log_invocation(args)
    
    if not args:
        print("Usage: agpair <doctor|daemon|task|approve|reject|continue|retry> ...")
        sys.exit(0)
    
    cmd = args[0]
    rest = args[1:]
    
    if cmd == "doctor":
        cmd_doctor(rest)
    elif cmd == "daemon":
        cmd_daemon(rest)
    elif cmd == "task":
        cmd_task(rest)
    elif cmd in ("approve", "reject", "continue", "retry"):
        cmd_semantic(cmd, rest)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
AGPAIR_EOF

chmod +x /usr/local/bin/agpair

echo "Mock agpair CLI installed at /usr/local/bin/agpair"
agpair --version 2>/dev/null || true

# Initialize git repo in payments_service for doctor check
cd /workspace/payments_service
git init -q
git config user.email "ci@test.local"
git config user.name "CI"
git add -A
git commit -q -m "initial commit" 2>/dev/null || true

echo "Setup complete."