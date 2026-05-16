#!/usr/bin/env bash
set -e

WORKSPACE="/workspace"

# Create the scripts directory if not present
mkdir -p "$WORKSPACE/scripts"

# --- Create the mock ngrok_preview.py script ---
# This simulates the real script's CLI interface as described in SKILL.md
cat > "$WORKSPACE/scripts/ngrok_preview.py" << 'PYEOF'
#!/usr/bin/env python3
"""
Mock implementation of ngrok_preview.py for sandbox testing.
Simulates the real script interface described in SKILL.md.
"""
import argparse
import json
import sys
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

SESSIONS_DIR = Path("/workspace/sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

def cmd_up(args):
    session_id = args.session_id or f"auto-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    ttl = args.ttl_minutes or 120
    title = args.title or "preview"
    sources = args.source or []

    # Validate sources exist
    for s in sources:
        if not Path(s).exists():
            print(json.dumps({"error": f"Source not found: {s}"}))
            sys.exit(1)

    expires_at = (datetime.utcnow() + timedelta(minutes=ttl)).strftime("%Y-%m-%dT%H:%M:%SZ")
    public_url = f"https://mock-preview-{session_id[:16].replace('/', '-')}.ngrok-free.app"
    stop_command = f"python3 scripts/ngrok_preview.py down --session-id {session_id} --delete-session-dir"

    session_data = {
        "public_url": public_url,
        "expires_at": expires_at,
        "session_id": session_id,
        "ttl_minutes": ttl,
        "title": title,
        "sources": sources,
        "stop_command": stop_command,
        "status": "active",
    }

    session_file = SESSIONS_DIR / f"{session_id.replace('/', '_')}.json"
    session_file.write_text(json.dumps(session_data, indent=2))

    print(json.dumps(session_data, indent=2))

def cmd_down(args):
    session_id = args.session_id
    if not session_id:
        # Find latest
        files = sorted(SESSIONS_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime)
        if not files:
            print(json.dumps({"error": "No active sessions found"}))
            sys.exit(1)
        session_file = files[-1]
    else:
        session_file = SESSIONS_DIR / f"{session_id.replace('/', '_')}.json"

    if not session_file.exists():
        print(json.dumps({"error": f"Session not found: {session_id}"}))
        sys.exit(1)

    data = json.loads(session_file.read_text())
    data["status"] = "stopped"

    if args.delete_session_dir:
        session_file.unlink()
        data["deleted"] = True
    else:
        session_file.write_text(json.dumps(data, indent=2))

    print(json.dumps({"status": "stopped", "session_id": data["session_id"], "deleted": args.delete_session_dir}))

def cmd_status(args):
    files = list(SESSIONS_DIR.glob("*.json"))
    sessions = [json.loads(f.read_text()) for f in files]
    print(json.dumps({"sessions": sessions}, indent=2))

def cmd_cleanup(args):
    now = datetime.utcnow()
    removed = []
    for f in SESSIONS_DIR.glob("*.json"):
        data = json.loads(f.read_text())
        expires = datetime.strptime(data.get("expires_at", "2000-01-01T00:00:00Z"), "%Y-%m-%dT%H:%M:%SZ")
        if expires < now:
            f.unlink()
            removed.append(data["session_id"])
    print(json.dumps({"cleaned_up": removed}))

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    up_p = subparsers.add_parser("up")
    up_p.add_argument("--title", default="preview")
    up_p.add_argument("--session-id", default=None)
    up_p.add_argument("--ttl-minutes", type=int, default=120)
    up_p.add_argument("--source", action="append", default=[])
    up_p.add_argument("--auth-token", default=None)

    down_p = subparsers.add_parser("down")
    down_p.add_argument("--session-id", default=None)
    down_p.add_argument("--delete-session-dir", action="store_true")

    subparsers.add_parser("status")
    subparsers.add_parser("cleanup")

    args = parser.parse_args()

    if args.command == "up":
        cmd_up(args)
    elif args.command == "down":
        cmd_down(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "cleanup":
        cmd_cleanup(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
PYEOF

chmod +x "$WORKSPACE/scripts/ngrok_preview.py"

echo "Mock ngrok_preview.py installed at $WORKSPACE/scripts/ngrok_preview.py"
echo "Workspace ready."