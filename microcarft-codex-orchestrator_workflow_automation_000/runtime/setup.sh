#!/usr/bin/env bash
set -e

STATE_DIR="/tmp/codex_mock_state"
mkdir -p "$STATE_DIR"
chmod 777 "$STATE_DIR"

# ─────────────────────────────────────────────────────────────────────────────
# Mock `codex` binary
# ─────────────────────────────────────────────────────────────────────────────
cat > /usr/local/bin/codex << 'CODEX_SCRIPT'
#!/usr/bin/env python3
"""
Mock codex binary.
Supports: codex exec --full-auto '<PROMPT>'
          codex resume <session_id>
          codex resume --last
"""
import sys
import os
import uuid
import json
import time
import threading

STATE_DIR = "/tmp/codex_mock_state"

def get_session_file(sid):
    return os.path.join(STATE_DIR, f"{sid}.json")

def load_session(sid):
    sf = get_session_file(sid)
    if os.path.exists(sf):
        with open(sf) as f:
            return json.load(f)
    return None

def save_session(data):
    sf = get_session_file(data["sessionId"])
    with open(sf, "w") as f:
        json.dump(data, f)

def simulate_work(sid):
    """Background thread: simulate session lifecycle."""
    import time
    session = load_session(sid)
    if not session:
        return

    # Phase 1: Working (3 seconds)
    logs = []
    logs.append("[codex] Session started.\n")
    logs.append("Working... analyzing legacy_bank_app/core/auth/login.py\n")
    logs.append("Thinking... identifying Python 2 patterns\n")
    logs.append("Edit legacy_bank_app/core/auth/login.py -> replaced md5 with hashlib\n")
    logs.append("Working... analyzing legacy_bank_app/core/transactions/transfer.py\n")
    logs.append("Edit legacy_bank_app/core/transactions/transfer.py -> replaced httplib with http.client\n")
    logs.append("Working... analyzing legacy_bank_app/utils/crypto.py\n")
    logs.append("Edit legacy_bank_app/utils/crypto.py -> replaced sha with hashlib\n")
    session["logs"] = "".join(logs)
    session["phase"] = "pre_prompt"
    save_session(session)
    time.sleep(3)

    # Phase 2: Stuck - emit interactive prompt
    session = load_session(sid)
    session["logs"] += "\nApply changes to legacy_bank_app/reporting/monthly.py? [y/n] "
    session["phase"] = "waiting_for_input"
    save_session(session)

    # Wait for submit (up to 60 seconds)
    for _ in range(120):
        time.sleep(0.5)
        session = load_session(sid)
        if session.get("submitted_data") is not None:
            break

    # Phase 3: After receiving input
    session = load_session(sid)
    submitted = session.get("submitted_data", "")
    if submitted.strip().lower() == "y" or submitted.strip() == "":
        session["logs"] += "y\n"
        session["logs"] += "Edit legacy_bank_app/reporting/monthly.py -> replaced cPickle/StringIO with pickle/io\n"
        session["logs"] += "Edit legacy_bank_app/utils/helpers.py -> replaced types.StringTypes with str\n"
        session["logs"] += "Running... verifying changes\n"
        session["logs"] += "[codex] Task completed successfully. 5 files modernized.\n"
        session["phase"] = "completed"
        session["files_changed"] = [
            "legacy_bank_app/core/auth/login.py",
            "legacy_bank_app/core/transactions/transfer.py",
            "legacy_bank_app/utils/crypto.py",
            "legacy_bank_app/reporting/monthly.py",
            "legacy_bank_app/utils/helpers.py"
        ]
    else:
        session["logs"] += "\n[codex] User declined. Skipping remaining changes.\n"
        session["phase"] = "completed_partial"
        session["files_changed"] = [
            "legacy_bank_app/core/auth/login.py",
            "legacy_bank_app/core/transactions/transfer.py",
            "legacy_bank_app/utils/crypto.py",
        ]
    save_session(session)

def cmd_exec(args):
    """Handle: codex exec --full-auto '<PROMPT>'"""
    sid = str(uuid.uuid4())[:8]
    workdir = os.environ.get("CODEX_WORKDIR", "/workspace")
    session = {
        "sessionId": sid,
        "phase": "starting",
        "logs": "",
        "submitted_data": None,
        "files_changed": [],
        "workdir": workdir,
        "prompt": " ".join(args),
    }
    save_session(session)
    print(f"sessionId: {sid}", flush=True)

    # Launch background thread to simulate work
    t = threading.Thread(target=simulate_work, args=(sid,), daemon=True)
    t.start()
    t.join()  # In PTY background mode, we just let it run
    sys.exit(0)

def cmd_resume(args):
    """Handle: codex resume --last | codex resume <sid>"""
    if not args:
        print("Usage: codex resume --last | codex resume <sid>")
        sys.exit(1)
    if args[0] == "--last":
        # Find most recent session file
        import glob
        files = sorted(glob.glob(os.path.join(STATE_DIR, "*.json")),
                       key=os.path.getmtime, reverse=True)
        if not files:
            print("No sessions found.")
            sys.exit(1)
        with open(files[0]) as f:
            session = json.load(f)
        sid = session["sessionId"]
    else:
        sid = args[0]

    session = load_session(sid)
    if not session:
        print(f"Session {sid} not found.")
        sys.exit(1)

    print(f"Resuming session {sid} (phase: {session.get('phase')})")
    if session.get("phase") not in ("completed", "completed_partial"):
        session["submitted_data"] = None
        save_session(session)
        t = threading.Thread(target=simulate_work, args=(sid,), daemon=True)
        t.start()
        t.join()
    else:
        print("Session already completed.")
    sys.exit(0)

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: codex <exec|resume> ...")
        sys.exit(1)

    if args[0] == "exec":
        cmd_exec(args[1:])
    elif args[0] == "resume":
        cmd_resume(args[1:])
    else:
        print(f"Unknown command: {args[0]}")
        sys.exit(1)
CODEX_SCRIPT

chmod +x /usr/local/bin/codex

# ─────────────────────────────────────────────────────────────────────────────
# Mock `process` binary
# ─────────────────────────────────────────────────────────────────────────────
cat > /usr/local/bin/process << 'PROCESS_SCRIPT'
#!/usr/bin/env python3
"""
Mock process binary.
Supports:
  process action:list
  process action:log sessionId:<sid> limit:<n>
  process action:submit sessionId:<sid> data:"<data>"
  process action:kill sessionId:<sid>
"""
import sys
import os
import json
import glob

STATE_DIR = "/tmp/codex_mock_state"

def parse_args(args):
    """Parse key:value style arguments."""
    result = {}
    for arg in args:
        if ":" in arg:
            key, _, val = arg.partition(":")
            result[key.strip()] = val.strip()
    return result

def get_session_file(sid):
    return os.path.join(STATE_DIR, f"{sid}.json")

def load_session(sid):
    sf = get_session_file(sid)
    if not os.path.exists(sf):
        return None
    with open(sf) as f:
        return json.load(f)

def save_session(data):
    sf = get_session_file(data["sessionId"])
    with open(sf, "w") as f:
        json.dump(data, f)

def record_action(action_name, sid, extra=None):
    """Record action history for evaluation purposes."""
    history_file = os.path.join(STATE_DIR, "action_history.jsonl")
    entry = {"action": action_name, "sessionId": sid}
    if extra:
        entry.update(extra)
    with open(history_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

def cmd_list():
    files = glob.glob(os.path.join(STATE_DIR, "*.json"))
    sessions = []
    for f in files:
        try:
            with open(f) as fp:
                s = json.load(fp)
            sessions.append({"sessionId": s["sessionId"], "phase": s.get("phase")})
        except Exception:
            pass
    if not sessions:
        print("No active sessions.")
    for s in sessions:
        print(f"  sessionId={s['sessionId']} phase={s['phase']}")

def cmd_log(params):
    sid = params.get("sessionId", "")
    limit_str = params.get("limit", "2000")
    try:
        limit = int(limit_str)
    except ValueError:
        limit = 2000

    session = load_session(sid)
    if not session:
        print(f"Session not found: {sid}")
        sys.exit(1)

    logs = session.get("logs", "")
    # Return last `limit` bytes
    output = logs[-limit:] if len(logs) > limit else logs
    print(output, end="")
    record_action("log", sid, {"limit": limit})

def cmd_submit(params):
    sid = params.get("sessionId", "")
    data = params.get("data", "")

    session = load_session(sid)
    if not session:
        print(f"Session not found: {sid}")
        sys.exit(1)

    session["submitted_data"] = data
    save_session(session)
    record_action("submit", sid, {"data": data})
    print(f"Submitted to session {sid}: {repr(data)}")

def cmd_kill(params):
    sid = params.get("sessionId", "")
    session = load_session(sid)
    if not session:
        print(f"Session not found: {sid}")
        sys.exit(1)

    session["phase"] = "killed"
    save_session(session)
    record_action("kill", sid)
    print(f"Session {sid} killed.")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: process action:<action> [key:val ...]")
        sys.exit(1)

    params = parse_args(args)
    action = params.get("action", "")

    if action == "list":
        cmd_list()
    elif action == "log":
        cmd_log(params)
    elif action == "submit":
        cmd_submit(params)
    elif action == "kill":
        cmd_kill(params)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
PROCESS_SCRIPT

chmod +x /usr/local/bin/process

# ─────────────────────────────────────────────────────────────────────────────
# Mock `bash` with PTY/background support
# ─────────────────────────────────────────────────────────────────────────────
# We rename the real bash and create a wrapper that intercepts pty:true syntax
mv /usr/local/bin/bash /usr/local/bin/bash_pty_mock 2>/dev/null || true

cat > /usr/local/bin/bash << 'BASH_SCRIPT'
#!/usr/bin/env python3
"""
Mock bash that intercepts `pty:true workdir:<dir> background:true command:"..."` syntax.
Falls through to real bash for all other invocations.
"""
import sys
import os
import subprocess
import re

def parse_pty_args(args):
    """Parse pty:true workdir:<dir> background:true command:"<cmd>" """
    joined = " ".join(args)
    result = {}

    # Extract pty
    m = re.search(r'\bpty:(true|false)\b', joined)
    if m:
        result["pty"] = m.group(1) == "true"

    # Extract workdir
    m = re.search(r'\bworkdir:(\S+)', joined)
    if m:
        result["workdir"] = m.group(1)

    # Extract background
    m = re.search(r'\bbackground:(true|false)\b', joined)
    if m:
        result["background"] = m.group(1) == "true"

    # Extract command (quoted or unquoted)
    m = re.search(r'\bcommand:"([^"]+)"', joined)
    if not m:
        m = re.search(r"\bcommand:'([^']+)'", joined)
    if not m:
        m = re.search(r'\bcommand:(\S+)', joined)
    if m:
        result["command"] = m.group(1)

    return result

def is_pty_invocation(args):
    joined = " ".join(args)
    return "pty:" in joined and "background:" in joined and "command:" in joined

def run_real_bash(args):
    real_bash = "/bin/bash"
    os.execv(real_bash, [real_bash] + args)

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or not is_pty_invocation(args):
        run_real_bash(args)

    params = parse_pty_args(args)
    command = params.get("command", "")
    workdir = params.get("workdir", "/workspace")
    background = params.get("background", False)
    pty = params.get("pty", False)

    if not command:
        print("Error: no command specified")
        sys.exit(1)

    # Record this invocation
    import json
    import time
    state_dir = "/tmp/codex_mock_state"
    os.makedirs(state_dir, exist_ok=True)
    launch_file = os.path.join(state_dir, "launch_history.jsonl")
    entry = {
        "command": command,
        "workdir": workdir,
        "pty": pty,
        "background": background,
        "timestamp": time.time()
    }
    with open(launch_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Set workdir env for codex mock
    env = os.environ.copy()
    env["CODEX_WORKDIR"] = workdir

    # Execute the command
    proc = subprocess.run(
        command,
        shell=True,
        env=env,
        cwd=workdir if os.path.isdir(workdir) else "/workspace",
        capture_output=False,
    )
    sys.exit(proc.returncode)
BASH_SCRIPT

chmod +x /usr/local/bin/bash

echo "Mock binaries installed successfully."
echo "  /usr/local/bin/bash  -> PTY-aware wrapper"
echo "  /usr/local/bin/codex -> Mock codex agent"
echo "  /usr/local/bin/process -> Mock process controller"