import json
import os
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# -----------------------------------------------------------------------
# Create distractor directory structure
# -----------------------------------------------------------------------
dirs = [
    "logs",
    "archive",
    "config",
    "scripts/helpers",
    "scripts/utils",
    "data/raw",
    "data/processed",
    "tmp",
    "notes",
    "backup/2024",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "notes/project_notes.txt": "Ongoing project notes. Remember to review invoices quarterly.\nContact billing@acmecorp.com for disputes.",
    "config/app_config.yaml": "app:\n  name: MailSorter\n  version: 1.2.0\n  max_retries: 3\ndebug: false\n",
    "config/labels.txt": "A_Personal\nA_Work\nA_Finance\nINBOX\nUNREAD\nCATEGORY_UPDATES\n",
    "data/raw/contacts.csv": "name,email,type\nJohn Smith,john@example.com,friend\nACME Corp,billing@acmecorp.com,vendor\nSchool Office,office@school.com,school\n",
    "data/processed/stats.json": json.dumps({"emails_processed": 142, "labels_applied": 98, "archived": 87}),
    "scripts/helpers/parse_email.sh": "#!/bin/bash\n# helper: parse email headers\necho \"$1\" | grep -i 'from:'\n",
    "scripts/utils/cleanup.py": "# Utility: clean up old temp files\nimport os, glob\nfor f in glob.glob('/tmp/*.tmp'):\n    os.remove(f)\n",
    "archive/old_run.log": "[2024-01-15 10:00:00] [INFO] Processed 5 emails\n[2024-01-15 10:00:01] [INFO] Applied label A_Personal/Finance to thread_abc\n",
    "tmp/session.lock": "locked=false\npid=0\n",
    "backup/2024/backup_manifest.json": json.dumps({"date": "2024-12-31", "files": 234, "size_mb": 12.4}),
    "notes/label_ideas.txt": "Possible labels to use:\n- A_Personal/Finance (for invoices)\n- A_Work/HR\n- A_Personal/Health\nNote: These are just brainstorms, not final.\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# -----------------------------------------------------------------------
# THE CORE STATE: emails_db.json
# This is the mock Gmail database that the `gog` CLI will read/write.
# -----------------------------------------------------------------------
# 
# Key scenario facts (agent must discover these by calling mock gog):
#   - 1 unread email from billing@acmecorp.com (thread_001)
#   - Archived emails from same sender: thread_099, thread_098 → both have A_Personal/Finance
#   - An INBOX (non-archived) email from same sender: thread_097 → has A_Work/Billing
#     (This is the trap: agent must ignore inbox emails when determining label pattern)
#   - Another archived email from billing@acmecorp.com: thread_096 → has label "Vendors" 
#     (not starting with A_Personal or A_Work → must be ignored in label selection)
#   - The unread email has labels: INBOX, UNREAD, CATEGORY_UPDATES

emails_db = {
    "messages": [
        {
            "id": "msg_001",
            "threadId": "thread_001",
            "subject": "Your invoice #INV-2025-0042 is ready",
            "from": "ACME Corp Billing <billing@acmecorp.com>",
            "snippet": "Please find attached your invoice for services rendered in June 2025.",
            "labels": ["INBOX", "UNREAD", "CATEGORY_UPDATES"],
            "archived": False,
            "body": "Dear Customer,\n\nPlease find attached your invoice #INV-2025-0042 for services rendered.\n\nAmount due: $450.00\nDue date: 2025-07-15\n\nThank you for your business.\n\nACME Corp Billing Team"
        },
        # Archived emails from billing@acmecorp.com with A_Personal/Finance
        {
            "id": "msg_099",
            "threadId": "thread_099",
            "subject": "Your invoice #INV-2025-0031 is ready",
            "from": "ACME Corp Billing <billing@acmecorp.com>",
            "snippet": "Invoice for May 2025.",
            "labels": ["A_Personal/Finance", "Vendors"],
            "archived": True,
            "body": "Invoice for May 2025. Amount: $420.00"
        },
        {
            "id": "msg_098",
            "threadId": "thread_098",
            "subject": "Your invoice #INV-2025-0019 is ready",
            "from": "ACME Corp Billing <billing@acmecorp.com>",
            "snippet": "Invoice for April 2025.",
            "labels": ["A_Personal/Finance"],
            "archived": True,
            "body": "Invoice for April 2025. Amount: $390.00"
        },
        # Non-archived (inbox) email from billing@acmecorp.com with A_Work/Billing
        # This is the TRAP — agent must NOT use this label since it's not archived
        {
            "id": "msg_097",
            "threadId": "thread_097",
            "subject": "Re: Invoice dispute #INV-2025-0010",
            "from": "ACME Corp Billing <billing@acmecorp.com>",
            "snippet": "Following up on your dispute.",
            "labels": ["INBOX", "A_Work/Billing"],
            "archived": False,
            "body": "Following up on dispute. Please respond."
        },
        # Archived email from billing@acmecorp.com with only "Vendors" label (not A_ prefix)
        # Agent must ignore this in label count
        {
            "id": "msg_096",
            "threadId": "thread_096",
            "subject": "Account statement Q1 2025",
            "from": "ACME Corp Billing <billing@acmecorp.com>",
            "snippet": "Q1 account statement attached.",
            "labels": ["Vendors"],
            "archived": True,
            "body": "Q1 2025 account statement. Total: $1200.00"
        },
        # Unrelated emails for realism
        {
            "id": "msg_050",
            "threadId": "thread_050",
            "subject": "Weekly newsletter",
            "from": "news@techdigest.io",
            "snippet": "This week in tech...",
            "labels": ["INBOX", "UNREAD", "CATEGORY_PROMOTIONS"],
            "archived": False,
            "body": "Tech news for the week..."
        },
        {
            "id": "msg_040",
            "threadId": "thread_040",
            "subject": "School event reminder",
            "from": "office@school.com",
            "snippet": "Don't forget the parent meeting.",
            "labels": ["A_Personal/School"],
            "archived": True,
            "body": "Parent-teacher meeting on Friday."
        },
    ]
}

emails_db_path = os.path.join(workspace, "emails_db.json")
with open(emails_db_path, "w") as f:
    json.dump(emails_db, f, indent=2)

# -----------------------------------------------------------------------
# Create the `gog` mock CLI
# -----------------------------------------------------------------------
gog_script = '''#!/usr/bin/env python3
import sys
import json
import os
import re

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emails_db.json")

def load_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

def cmd_gmail_messages_search(args):
    # Handle: gog gmail messages search <query> --max N --json
    query = ""
    max_results = 20
    output_json = False
    i = 0
    positional = []
    while i < len(args):
        if args[i] == "--max" and i+1 < len(args):
            max_results = int(args[i+1])
            i += 2
        elif args[i] == "--json":
            output_json = True
            i += 1
        else:
            positional.append(args[i])
            i += 1

    if positional:
        query = positional[0]

    db = load_db()
    messages = db["messages"]

    # Parse query
    is_unread = "is:unread" in query
    is_archived = "is:archived" in query
    from_match = re.search(r\'from:"([^"]+)"\', query)
    from_filter = from_match.group(1) if from_match else None

    results = []
    for msg in messages:
        if is_unread and "UNREAD" not in msg["labels"]:
            continue
        if is_archived and not msg.get("archived", False):
            continue
        if from_filter and from_filter.lower() not in msg["from"].lower():
            continue
        results.append(msg)

    results = results[:max_results]

    output = {"messages": results}
    print(json.dumps(output))

def cmd_gmail_thread_get(args):
    # Handle: gog gmail thread get <threadId> --full --json
    thread_id = None
    i = 0
    while i < len(args):
        if args[i] in ("--full", "--json"):
            i += 1
        else:
            thread_id = args[i]
            i += 1

    if not thread_id:
        print(json.dumps({"error": "No thread ID"}))
        sys.exit(1)

    db = load_db()
    for msg in db["messages"]:
        if msg["threadId"] == thread_id:
            print(json.dumps(msg))
            return

    print(json.dumps({"error": f"Thread {thread_id} not found"}))
    sys.exit(1)

def cmd_gmail_thread_modify(args):
    # Handle: gog gmail thread modify <threadId> --add <label> OR --remove <labels>
    thread_id = None
    add_label = None
    remove_labels = None
    i = 0
    positional = []
    while i < len(args):
        if args[i] == "--add" and i+1 < len(args):
            add_label = args[i+1]
            i += 2
        elif args[i] == "--remove" and i+1 < len(args):
            remove_labels = args[i+1]
            i += 2
        else:
            positional.append(args[i])
            i += 1

    if positional:
        thread_id = positional[0]

    if not thread_id:
        print("Error: No thread ID provided", file=sys.stderr)
        sys.exit(1)

    db = load_db()
    modified = False
    for msg in db["messages"]:
        if msg["threadId"] == thread_id:
            if add_label:
                if add_label not in msg["labels"]:
                    msg["labels"].append(add_label)
                modified = True
            if remove_labels:
                labels_to_remove = [l.strip() for l in remove_labels.split(",")]
                for lbl in labels_to_remove:
                    if lbl in msg["labels"]:
                        msg["labels"].remove(lbl)
                    # Handle INBOX removal => mark as archived
                    if lbl == "INBOX":
                        msg["archived"] = True
                modified = True

    if modified:
        save_db(db)
        print(f"Thread {thread_id} modified successfully")
    else:
        print(f"Warning: Thread {thread_id} not found", file=sys.stderr)
        sys.exit(1)

def main():
    args = sys.argv[1:]
    if len(args) < 3:
        print("Usage: gog <service> <resource> <command> [args...]", file=sys.stderr)
        sys.exit(1)

    service = args[0]   # gmail
    resource = args[1]  # messages | thread
    command = args[2]   # search | get | modify
    rest = args[3:]

    if service == "gmail":
        if resource == "messages" and command == "search":
            cmd_gmail_messages_search(rest)
        elif resource == "thread" and command == "get":
            cmd_gmail_thread_get(rest)
        elif resource == "thread" and command == "modify":
            cmd_gmail_thread_modify(rest)
        else:
            print(f"Unknown command: {resource} {command}", file=sys.stderr)
            sys.exit(1)
    elif service == "calendar":
        # Stub: just acknowledge
        print("Calendar event noted (stub)")
    else:
        print(f"Unknown service: {service}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

gog_path = os.path.join(workspace, "gog")
with open(gog_path, "w") as f:
    f.write(gog_script)
os.chmod(gog_path, os.stat(gog_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# -----------------------------------------------------------------------
# Place script.sh in workspace (as referenced by SKILL.md)
# -----------------------------------------------------------------------
# The agent needs to READ this to understand the workflow.
# script.sh content references gog and the overall logic.
# We create a simplified but complete version.

script_sh_path = os.path.join(workspace, "script.sh")

# Write the actual script.sh (condensed version with the key workflow)
script_sh_content = r"""#!/bin/bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="${SCRIPT_DIR}/logs"
readonly LOG_FILE="${LOG_DIR}/gmail-label-log.txt"
readonly MAX_EMAILS=1

readonly LABEL_PREFIX="A_Personal,A_Work"
readonly REMOVE_LABELS="CATEGORY_UPDATES,CATEGORY_PROMOTIONS,UNREAD"

mkdir -p "$LOG_DIR"

log() {
  local level="${1:-INFO}"
  shift
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}
log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@" >&2; }

get_unread_emails() {
  gog gmail messages search "is:unread" --max "$MAX_EMAILS" --json
}

get_thread_content() {
  gog gmail thread get "$1" --full --json
}

apply_label() {
  gog gmail thread modify "$1" --add "$2"
}

remove_labels() {
  gog gmail thread modify "$1" --remove "$REMOVE_LABELS"
}

archive_email() {
  gog gmail thread modify "$1" --remove INBOX
}

get_label_pattern() {
  local sender="$1"
  local archived_emails
  archived_emails=$(gog gmail messages search "is:archived from:\"${sender}\"" --max 20 --json 2>&1)
  if [ $? -ne 0 ]; then
    echo ""
    return 1
  fi
  local label_pattern
  label_pattern=$(echo "$archived_emails" | jq -r "
    [.messages[]? | .labels[]? | select(startswith(\"A_Personal\") or startswith(\"A_Work\"))]
    | group_by(.)
    | map({label: .[0], count: length})
    | sort_by(.count)
    | reverse
    | .[0].label // empty
  ")
  echo "$label_pattern"
}

process_single_email() {
  local email_json="$1"
  local email_id thread_id subject sender
  email_id=$(echo "$email_json" | jq -r '.id // empty')
  thread_id=$(echo "$email_json" | jq -r '.threadId // empty')
  subject=$(echo "$email_json" | jq -r '.subject // "(No Subject)"')
  sender=$(echo "$email_json" | jq -r '.from // "unknown"')

  if [ -z "$email_id" ] || [ -z "$thread_id" ]; then
    log_warn "Skipping email with missing ID or thread ID"
    return 1
  fi

  log_info "Processing: $subject from $sender (thread: $thread_id)"

  local label_pattern
  label_pattern=$(get_label_pattern "$sender")

  local label_applied=false
  if [ -n "$label_pattern" ]; then
    log_info "Applying label: $label_pattern"
    if apply_label "$thread_id" "$label_pattern"; then
      label_applied=true
    fi
  else
    log_info "No label pattern found for sender"
  fi

  remove_labels "$thread_id"

  if [ "$label_applied" = true ]; then
    archive_email "$thread_id"
  else
    log_info "Email not archived (no label found)"
  fi

  log_info "Email processing completed for thread $thread_id"
  return 0
}

main() {
  log_info "Gmail Manager Started"
  local unread_emails
  unread_emails=$(get_unread_emails)
  local email_count
  email_count=$(echo "$unread_emails" | jq '.messages | length')
  log_info "Found $email_count unread email(s)"

  for i in $(seq 0 $((email_count - 1))); do
    local email_json
    email_json=$(echo "$unread_emails" | jq ".messages[$i]")
    process_single_email "$email_json" || log_warn "Failed to process email $((i+1))"
  done

  log_info "Gmail Manager Finished"
}

main "$@"
"""

with open(script_sh_path, "w") as f:
    f.write(script_sh_content)
os.chmod(script_sh_path, os.stat(script_sh_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

print("Workspace setup complete.")
print(f"  - emails_db.json created at {emails_db_path}")
print(f"  - gog mock CLI created at {gog_path}")
print(f"  - script.sh created at {script_sh_path}")
print(f"  - {len(distractor_files)} distractor files created")