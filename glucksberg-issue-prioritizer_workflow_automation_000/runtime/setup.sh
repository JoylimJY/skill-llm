#!/bin/bash
set -e

# Ensure mock gh binary is executable
chmod +x /usr/local/bin/gh

# Verify mock gh works
echo "Verifying mock gh CLI..."
gh auth status && echo "gh auth: OK"
gh issue list --repo datapipe-org/datapipe-cli --state open --limit 10 --json number,title | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Issues available: {len(d)}')"
gh pr list --repo datapipe-org/datapipe-cli --state open --json number,title | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'PRs available: {len(d)}')"

echo "Setup complete. Workspace ready for agent."