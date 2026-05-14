#!/bin/bash
set -e

# ─── Create a mock `reskill` binary that simulates the real CLI ───────────────
# This mock logs every call and returns deterministic JSON responses.

mkdir -p /usr/local/bin

cat > /usr/local/bin/reskill << 'MOCK_RESKILL_EOF'
#!/usr/bin/env python3
"""
Mock reskill CLI for evaluation purposes.
Logs all invocations and returns deterministic responses.
"""
import sys
import json
import os
import datetime

LOG_FILE = "/tmp/reskill_calls.log"
INSTALL_LOG = "/tmp/reskill_installs.log"

args = sys.argv[1:]

def log_call(args):
    with open(LOG_FILE, "a") as f:
        ts = datetime.datetime.utcnow().isoformat()
        f.write(json.dumps({"timestamp": ts, "args": args}) + "\n")

def cmd_find(args):
    """Handle: reskill find <query> [--json] [--registry <url>]"""
    # Extract query (first positional after 'find')
    query = None
    json_mode = False
    i = 0
    while i < len(args):
        if args[i] == "--json":
            json_mode = True
        elif args[i] == "--registry":
            i += 1  # skip registry value
        elif not args[i].startswith("--"):
            if query is None:
                query = args[i]
        i += 1

    query_lower = query.lower() if query else ""

    # Deterministic responses based on query
    if query_lower in ["deployment automation", "deployment-automation"]:
        result = {"total": 0, "items": []}
    elif query_lower in ["deployment", "deploy", "ci-cd", "devops"]:
        result = {
            "total": 2,
            "items": [
                {
                    "name": "@devops/ci-deploy",
                    "description": "Automated CI/CD deployment pipeline management for agent workflows",
                    "latest_version": "2.1.0",
                    "keywords": ["deploy", "ci-cd", "devops", "pipeline"],
                    "publisher": {"handle": "devops-team"},
                    "updated_at": "2025-01-15T00:00:00Z"
                },
                {
                    "name": "@ui/design-helper",
                    "description": "UI component design assistance and style guide generation",
                    "latest_version": "1.0.0",
                    "keywords": ["design", "ui", "components", "style"],
                    "publisher": {"handle": "ui-team"},
                    "updated_at": "2025-01-10T00:00:00Z"
                }
            ]
        }
    elif query_lower in ["automation"]:
        result = {"total": 0, "items": []}
    else:
        result = {"total": 0, "items": []}

    if json_mode:
        print(json.dumps(result, indent=2))
    else:
        if result["total"] == 0:
            print("No skills found.")
        else:
            for item in result["items"]:
                print(f"{item['name']} - {item['description']} (v{item['latest_version']})")

def cmd_list(args):
    """Handle: reskill list"""
    json_mode = "--json" in args
    result = {"total": 0, "items": []}
    if json_mode:
        print(json.dumps(result, indent=2))
    else:
        print("No skills installed.")

def cmd_install(args):
    """Handle: reskill install <name> [-y] [-a <agents...>] [--registry <url>] [-g]"""
    # Log the install command with all its arguments
    with open(INSTALL_LOG, "a") as f:
        ts = datetime.datetime.utcnow().isoformat()
        f.write(json.dumps({"timestamp": ts, "install_args": args}) + "\n")

    # Parse skill name
    skill_name = None
    agents = []
    global_install = False
    yes_flag = False
    registry = None
    i = 0
    while i < len(args):
        if args[i] == "-y":
            yes_flag = True
        elif args[i] == "-g":
            global_install = True
        elif args[i] in ["-a", "--agent"]:
            # collect all following non-flag args as agents
            i += 1
            while i < len(args) and not args[i].startswith("-"):
                agents.append(args[i])
                i += 1
            continue
        elif args[i] == "--registry":
            i += 1
            if i < len(args):
                registry = args[i]
        elif not args[i].startswith("-"):
            if skill_name is None:
                skill_name = args[i]
        i += 1

    print(f"Installing {skill_name}...")
    if agents:
        print(f"Target agents: {', '.join(agents)}")
    if global_install:
        print("Installing globally.")
    print(f"Successfully installed {skill_name} v2.1.0")

def cmd_info(args):
    skill = args[0] if args else "unknown"
    print(f"Skill: {skill}")
    print("No information available for this skill.")

# Main dispatch
log_call(args)

if not args:
    print("Usage: reskill <command> [options]")
    sys.exit(1)

command = args[0]
rest = args[1:]

if command == "find":
    cmd_find(rest)
elif command == "list":
    cmd_list(rest)
elif command == "install":
    cmd_install(rest)
elif command == "info":
    cmd_info(rest)
else:
    print(f"Unknown command: {command}")
    sys.exit(1)
MOCK_RESKILL_EOF

chmod +x /usr/local/bin/reskill

# Verify mock is accessible
echo "Mock reskill installed at: $(which reskill)"
reskill list

# Initialize log files
touch /tmp/reskill_calls.log
touch /tmp/reskill_installs.log
chmod 666 /tmp/reskill_calls.log
chmod 666 /tmp/reskill_installs.log

echo "Setup complete. Mock reskill ready."
echo "Workspace prepared at /workspace"