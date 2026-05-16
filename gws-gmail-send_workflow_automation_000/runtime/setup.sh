#!/bin/bash
set -e

# Create the mock `gws` binary that captures all arguments and simulates the real tool
cat > /usr/local/bin/gws << 'MOCK_GWS_EOF'
#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime

LOG_FILE = "/workspace/.gws_mock/calls.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

args = sys.argv[1:]

# Log the exact invocation
entry = {
    "timestamp": datetime.utcnow().isoformat(),
    "args": args,
    "raw_command": " ".join(sys.argv)
}

with open(LOG_FILE, "a") as f:
    f.write(json.dumps(entry) + "\n")

# Simulate realistic gws output
if len(args) >= 2 and args[0] == "gmail" and args[1] == "+send":
    if "--dry-run" in args:
        print("DRY RUN: Would send email with the following parameters:")
        i = 2
        while i < len(args):
            print(f"  {args[i]}", end="")
            if i+1 < len(args) and not args[i+1].startswith("--") and not args[i+1].startswith("-"):
                print(f" {args[i+1]}")
                i += 2
            else:
                print()
                i += 1
    elif "--draft" in args:
        print("Draft saved successfully.")
    else:
        # Find --to value for the success message
        to_val = ""
        for idx, a in enumerate(args):
            if a == "--to" and idx+1 < len(args):
                to_val = args[idx+1]
        print(f"Email sent successfully to: {to_val}")
elif len(args) >= 1 and args[0] == "generate-skills":
    print("Skills generated.")
elif len(args) >= 1 and (args[-1] == "--help" or "-h" in args):
    print("gws gmail +send --to <EMAILS> --subject <SUBJECT> --body <TEXT> [options]")
else:
    print(f"gws: executed with args: {' '.join(args)}")

sys.exit(0)
MOCK_GWS_EOF

chmod +x /usr/local/bin/gws

# Verify mock is working
echo "Mock gws binary installed at $(which gws)"
gws --help

echo "Setup complete. Workspace ready for agent."