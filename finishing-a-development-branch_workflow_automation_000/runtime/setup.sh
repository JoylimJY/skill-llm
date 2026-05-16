#!/usr/bin/env bash
set -euo pipefail

# Ensure git global config is set (may be needed after container restart)
git config --global user.email "agent@test.local"
git config --global user.name "Test Agent"
git config --global init.defaultBranch main

# Make scripts executable
chmod +x /workspace/fintech-pipeline/scripts/health_check.sh 2>/dev/null || true

# Install a mock 'gh' CLI so the agent can call `gh pr create` without real auth
cat > /usr/local/bin/gh << 'GHEOF'
#!/usr/bin/env bash
# Mock GitHub CLI - records the call and exits successfully
echo "[mock-gh] Called with args: $*" >&2
LOGFILE="/workspace/gh_calls.log"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) gh $*" >> "$LOGFILE"
if [[ "$*" == *"pr create"* ]]; then
    echo "https://github.com/fintech-example/fintech-pipeline/pull/42"
fi
exit 0
GHEOF
chmod +x /usr/local/bin/gh

# Verify the repo state is healthy before handing to agent
echo "=== Repo state at task start ==="
cd /workspace/fintech-pipeline
git worktree list
git branch -a
echo "=== Pytest check from worktree ==="
cd /workspace/worktrees/currency-converter
python -m pytest --tb=short -q 2>&1 | tail -5
echo "=== Setup complete ==="