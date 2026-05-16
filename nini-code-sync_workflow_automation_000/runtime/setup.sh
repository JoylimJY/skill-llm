#!/bin/bash
set -euo pipefail

# Ensure scripts are executable
chmod +x /workspace/scripts/scan.sh 2>/dev/null || true
chmod +x /workspace/scripts/git_wrapper.sh 2>/dev/null || true

# Initialize git pull log
touch /tmp/git_pull_log.txt
touch /tmp/git_merge_log.txt

# Configure git global settings
git config --global user.email "agent@fintech.local"
git config --global user.name "Agent Bot"
git config --global init.defaultBranch main

# Make sure the config store repo remote is properly unreachable for auth-gateway
# The remote is already set to 192.0.2.1 (TEST-NET, guaranteed unreachable)
# Verify scan.sh can be run
echo "Verifying scan.sh..."
cd /workspace
bash scripts/scan.sh --base-dir /workspace/code --fetch 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'scan.sh found {len(data)} repos')
for r in data:
    print(f\"  {r['name']}: dirty={r['dirty_count']}, ahead={r['ahead']}, behind={r['behind']}, fetch_error={r.get('fetch_error', False)}\")
" || echo "scan.sh verification had issues (may be expected for fetch errors)"

echo ""
echo "=== Workspace ready for agent ==="
echo "Working directory: /workspace"
echo "Git repos: /workspace/code/*"
echo "Config: ~/.config/nini-skill/code-sync/config.md"
echo ""