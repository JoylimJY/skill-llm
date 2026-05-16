#!/bin/bash
set -e

SKILL_DIR="/root/.openclaw/workspace/skills/lel-mail/scripts"
QUEUE_DIR="/root/.openclaw/workspace/skills/lel-mail/queue"

mkdir -p "$SKILL_DIR"
mkdir -p "$QUEUE_DIR"

# -----------------------------------------------------------------------
# Mock email_send.sh
# Writes a JSON file to the queue dir simulating the scheduler behavior.
# Supports: --sender --recipient --subject --body --cc --bcc
# -----------------------------------------------------------------------
cat > "$SKILL_DIR/email_send.sh" << 'SENDSCRIPT'
#!/bin/bash

SENDER=""
RECIPIENT=""
SUBJECT=""
BODY=""
CC=""
BCC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sender)    SENDER="$2";    shift 2 ;;
        --recipient) RECIPIENT="$2"; shift 2 ;;
        --subject)   SUBJECT="$2";   shift 2 ;;
        --body)      BODY="$2";      shift 2 ;;
        --cc)        CC="$2";        shift 2 ;;
        --bcc)       BCC="$2";       shift 2 ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$SENDER" || -z "$RECIPIENT" || -z "$SUBJECT" || -z "$BODY" ]]; then
    echo "ERROR: --sender, --recipient, --subject, and --body are required." >&2
    exit 1
fi

QUEUE_DIR="/root/.openclaw/workspace/skills/lel-mail/queue"
mkdir -p "$QUEUE_DIR"

# Generate a unique ID
EMAIL_ID=$(python3 -c "import uuid; print(uuid.uuid4().hex[:8])")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S")

python3 - <<PYEOF
import json, os
data = {
    "id": "$EMAIL_ID",
    "sender": "$SENDER",
    "recipient": "$RECIPIENT",
    "subject": "$SUBJECT",
    "body": "$BODY",
    "cc": "$CC",
    "bcc": "$BCC",
    "queued_at": "$TIMESTAMP"
}
path = os.path.join("$QUEUE_DIR", f"$EMAIL_ID.json")
with open(path, "w") as f:
    json.dump(data, f, indent=2)
print(f"Email queued successfully with ID: $EMAIL_ID")
print(f"It will be sent in approximately 30-90 seconds by the daemon.")
PYEOF
SENDSCRIPT

chmod +x "$SKILL_DIR/email_send.sh"

# -----------------------------------------------------------------------
# Mock manage_queue.py
# --list : prints all queued emails in a formatted table with IDs
# --delete <ID> : removes the specified email from the queue
# -----------------------------------------------------------------------
cat > "$SKILL_DIR/manage_queue.py" << 'PYEOF'
#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

QUEUE_DIR = Path("/root/.openclaw/workspace/skills/lel-mail/queue")

def list_queue():
    files = sorted(QUEUE_DIR.glob("*.json"))
    if not files:
        print("No emails in queue.")
        return
    print(f"{'ID':<12} {'SENDER':<30} {'RECIPIENT':<30} {'SUBJECT':<40} {'QUEUED_AT':<22}")
    print("-" * 134)
    for f in files:
        try:
            with open(f) as fh:
                data = json.load(fh)
            print(f"{data.get('id','?'):<12} {data.get('sender','?'):<30} {data.get('recipient','?'):<30} {data.get('subject','?'):<40} {data.get('queued_at','?'):<22}")
        except Exception as e:
            print(f"Error reading {f}: {e}")

def delete_email(email_id):
    target = QUEUE_DIR / f"{email_id}.json"
    if not target.exists():
        # Also try searching all files for matching id field
        found = False
        for f in QUEUE_DIR.glob("*.json"):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                if data.get("id") == email_id:
                    f.unlink()
                    print(f"Email {email_id} deleted from queue.")
                    found = True
                    break
            except Exception:
                pass
        if not found:
            print(f"ERROR: No email with ID '{email_id}' found in queue.", file=sys.stderr)
            sys.exit(1)
    else:
        target.unlink()
        print(f"Email {email_id} deleted from queue.")

def main():
    parser = argparse.ArgumentParser(description="Manage the lel-mail outgoing queue")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List all queued emails")
    group.add_argument("--delete", metavar="ID", help="Delete a queued email by ID")
    args = parser.parse_args()

    if args.list:
        list_queue()
    elif args.delete:
        delete_email(args.delete)

if __name__ == "__main__":
    main()
PYEOF

chmod +x "$SKILL_DIR/manage_queue.py"

# -----------------------------------------------------------------------
# Mock check_email.sh (not required for this task but must exist)
# -----------------------------------------------------------------------
cat > "$SKILL_DIR/check_email.sh" << 'CHECKSCRIPT'
#!/bin/bash
echo "Checking email for: $1"
echo "No new messages."
CHECKSCRIPT
chmod +x "$SKILL_DIR/check_email.sh"

# -----------------------------------------------------------------------
# Mock email_sender_daemon.sh
# -----------------------------------------------------------------------
cat > "$SKILL_DIR/email_sender_daemon.sh" << 'DAEMONSCRIPT'
#!/bin/bash
echo "Daemon: scanning queue..."
echo "No emails ready to send."
DAEMONSCRIPT
chmod +x "$SKILL_DIR/email_sender_daemon.sh"

echo "Setup complete. Mock scripts installed."
echo "Queue contents:"
ls /root/.openclaw/workspace/skills/lel-mail/queue/