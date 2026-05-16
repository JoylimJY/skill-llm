#!/usr/bin/env bash
set -e

# Create a mock `gws` binary that simulates the real CLI behavior
# and logs all invocations so the eval script can verify correct usage.

GWS_LOG="/tmp/gws_invocations.log"
GWS_UPLOADS_LOG="/tmp/gws_uploads.json"

# Initialize logs
echo "[]" > "$GWS_UPLOADS_LOG"
touch "$GWS_LOG"

cat > /usr/local/bin/gws << 'GWSEOF'
#!/usr/bin/env python3
import sys
import os
import json
import datetime

LOG_FILE = "/tmp/gws_invocations.log"
UPLOADS_FILE = "/tmp/gws_uploads.json"
CREDS_FILE = os.path.expanduser("~/.gws/credentials.json")

args = sys.argv[1:]

# Log raw invocation
with open(LOG_FILE, "a") as f:
    f.write(" ".join(["gws"] + args) + "\n")

# --- Parse and handle the command ---

def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def load_uploads():
    try:
        with open(UPLOADS_FILE) as f:
            return json.load(f)
    except Exception:
        return []

def save_upload(record):
    uploads = load_uploads()
    uploads.append(record)
    with open(UPLOADS_FILE, "w") as f:
        json.dump(uploads, f, indent=2)

# Require at least: drive +upload <subcommands>
if len(args) < 1:
    print("Usage: gws <service> <command> [options]")
    sys.exit(0)

# Handle generate-skills (no-op)
if args[0] == "generate-skills":
    print("Skills already up to date.")
    sys.exit(0)

# Check for --account flag (required per gws-shared)
account = None
remaining_args = []
i = 0
while i < len(args):
    if args[i] == "--account" and i + 1 < len(args):
        account = args[i+1]
        i += 2
    else:
        remaining_args.append(args[i])
        i += 1

if account is None:
    # Check credentials file for default (but CLI --account is required per shared skill)
    die("Missing required flag: --account. See gws-shared SKILL.md for auth requirements.")

# Validate account against credentials
if os.path.exists(CREDS_FILE):
    with open(CREDS_FILE) as f:
        creds = json.load(f)
    if creds.get("account") != account:
        die(f"Account '{account}' does not match credentials file account '{creds.get('account')}'.")
else:
    die("Credentials file not found at ~/.gws/credentials.json")

# Now parse remaining_args for: drive +upload <file> [--parent X] [--name Y]
if len(remaining_args) < 2:
    print("Usage: gws drive +upload <file> [--parent FOLDER_ID] [--name FILENAME]")
    sys.exit(1)

service = remaining_args[0]  # "drive"
command = remaining_args[1]  # "+upload"

if service != "drive":
    die(f"Unknown service: {service}")

if command != "+upload":
    die(f"Unknown command: {command}. Did you mean '+upload'?")

# Parse +upload specific args
upload_args = remaining_args[2:]

file_path = None
parent_id = None
target_name = None

j = 0
while j < len(upload_args):
    if upload_args[j] == "--parent" and j + 1 < len(upload_args):
        parent_id = upload_args[j+1]
        j += 2
    elif upload_args[j] == "--name" and j + 1 < len(upload_args):
        target_name = upload_args[j+1]
        j += 2
    elif not upload_args[j].startswith("--"):
        file_path = upload_args[j]
        j += 1
    else:
        die(f"Unknown flag: {upload_args[j]}")

if file_path is None:
    die("Missing required argument: <file>")

if not os.path.exists(file_path):
    die(f"File not found: {file_path}")

# Infer uploaded filename
if target_name is None:
    target_name = os.path.basename(file_path)

# Record the upload
record = {
    "timestamp": datetime.datetime.utcnow().isoformat(),
    "file_path": os.path.abspath(file_path),
    "account": account,
    "parent_id": parent_id,
    "uploaded_name": target_name,
    "file_size_bytes": os.path.getsize(file_path)
}

save_upload(record)

print(f"✓ Uploaded '{os.path.basename(file_path)}' as '{target_name}'")
if parent_id:
    print(f"  → Parent folder: {parent_id}")
print(f"  → Account: {account}")
print(f"  → File ID: mock-file-id-{hash(file_path) % 999999:06d}")
GWSEOF

chmod +x /usr/local/bin/gws

echo "Mock gws binary installed at /usr/local/bin/gws"
echo "Invocation log: /tmp/gws_invocations.log"
echo "Upload records: /tmp/gws_uploads.json"

# Verify it works
gws --account "finance-bot@acmecorp.com" drive +upload /dev/null 2>&1 || true
# Reset logs after test
echo "[]" > /tmp/gws_uploads.json
echo "" > /tmp/gws_invocations.log
echo "Setup complete."