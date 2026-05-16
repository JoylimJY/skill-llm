#!/usr/bin/env bash
set -e

# Create a mock `clawhub` CLI that records calls and simulates the slug-conflict scenario.
# First call to `clawhub publish` with slug `obsidian-daily` will fail with the conflict error.
# Subsequent call with slug `obsidian-daily-mai` will succeed.

mkdir -p /usr/local/lib/clawhub-mock

cat > /usr/local/lib/clawhub-mock/clawhub_state.json << 'EOF'
{"publish_attempts": []}
EOF

cat > /usr/local/bin/clawhub << 'CLAWHUB_SCRIPT'
#!/usr/bin/env python3
import sys
import json
import os

STATE_FILE = "/usr/local/lib/clawhub-mock/clawhub_state.json"

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

args = sys.argv[1:]

if not args:
    print("clawhub: missing subcommand")
    sys.exit(1)

cmd = args[0]

if cmd == "whoami":
    print("jini92")
    sys.exit(0)

if cmd == "login":
    print("Already logged in as jini92")
    sys.exit(0)

if cmd == "publish":
    # Parse arguments
    state = load_state()
    
    # Build a record of this call
    call_record = {"args": args}
    
    slug = None
    name = None
    version = None
    changelog = None
    skill_path = None
    
    i = 1
    while i < len(args):
        if args[i] == "--slug" and i+1 < len(args):
            slug = args[i+1]; i += 2
        elif args[i] == "--name" and i+1 < len(args):
            name = args[i+1]; i += 2
        elif args[i] == "--version" and i+1 < len(args):
            version = args[i+1]; i += 2
        elif args[i] == "--changelog" and i+1 < len(args):
            changelog = args[i+1]; i += 2
        else:
            if not skill_path and not args[i].startswith("--"):
                skill_path = args[i]
            i += 1
    
    call_record["slug"] = slug
    call_record["name"] = name
    call_record["version"] = version
    call_record["changelog"] = changelog
    call_record["skill_path"] = skill_path
    
    state["publish_attempts"].append(call_record)
    save_state(state)
    
    # Simulate slug conflict for base slug
    if slug == "obsidian-daily":
        print("Error: Only the owner can publish updates to 'obsidian-daily'")
        sys.exit(1)
    elif slug == "obsidian-daily-mai":
        print(f"Successfully published '{name}' v{version} as '{slug}'")
        print(f"View at: https://clawhub.ai/skills/{slug}")
        sys.exit(0)
    else:
        # Any other slug: simulate success (agent might use a different slug)
        print(f"Successfully published '{name}' v{version} as '{slug}'")
        sys.exit(0)

print(f"clawhub: unknown command '{cmd}'")
sys.exit(1)
CLAWHUB_SCRIPT

chmod +x /usr/local/bin/clawhub

echo "Mock clawhub CLI installed."
clawhub whoami