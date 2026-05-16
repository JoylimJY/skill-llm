#!/usr/bin/env bash
set -e

# Create the mock openclaw binary that logs all invocations
cat > /usr/local/bin/openclaw << 'MOCK_EOF'
#!/usr/bin/env python3
"""
Mock openclaw CLI — logs all invocations to /workspace/openclaw_calls.log
Simulates realistic success/failure responses.
"""
import sys
import os
import json
from datetime import datetime

LOG_PATH = "/workspace/openclaw_calls.log"
args = sys.argv[1:]
cmd_line = " ".join(args)

# Append to log
with open(LOG_PATH, "a") as f:
    f.write(cmd_line + "\n")

# Simulate responses
if not args:
    print("openclaw: missing subcommand", file=sys.stderr)
    sys.exit(1)

if args[0] == "agents":
    if len(args) < 2:
        print("openclaw agents: missing action", file=sys.stderr)
        sys.exit(1)
    action = args[1]

    if action == "list":
        print("Agents:\n  helperbot (active)\n  support-alpha (decommissioned)")
        sys.exit(0)

    elif action == "add":
        if len(args) < 3:
            print("ERROR: agent name required", file=sys.stderr)
            sys.exit(1)
        name = args[2]
        print(f"Agent '{name}' created successfully.")
        sys.exit(0)

    elif action == "bind":
        print("Binding updated successfully.")
        sys.exit(0)

    elif action == "unbind":
        print("Binding removed successfully.")
        sys.exit(0)

    elif action == "delete":
        if len(args) < 3:
            print("ERROR: agent name required", file=sys.stderr)
            sys.exit(1)
        name = args[2]
        print(f"Agent '{name}' deleted.")
        sys.exit(0)

    elif action == "set-identity":
        print("Identity updated.")
        sys.exit(0)

    else:
        print(f"openclaw agents: unknown action '{action}'", file=sys.stderr)
        sys.exit(1)

else:
    print(f"openclaw: unknown command '{args[0]}'", file=sys.stderr)
    sys.exit(1)
MOCK_EOF

chmod +x /usr/local/bin/openclaw

# Verify mock works
openclaw agents list > /dev/null 2>&1 && echo "Mock openclaw verified OK" || echo "WARNING: mock openclaw check failed"

echo "Setup complete."