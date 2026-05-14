#!/usr/bin/env bash
set -euo pipefail

# ── 1. Git global config (idempotent) ──────────────────────────────────────
git config --global user.email "agent@test.local"
git config --global user.name "Agent Test"
git config --global init.defaultBranch main

# ── 2. Install a fake 'gh' CLI stub ────────────────────────────────────────
# The real 'gh' would need auth; we provide a stub that records invocations
cat > /usr/local/bin/gh << 'GHEOF'
#!/usr/bin/env bash
# Fake GitHub CLI - records all calls for evaluation
LOG_FILE="/workspace/.gh_calls.log"
echo "gh $*" >> "$LOG_FILE"

if [[ "${1:-}" == "pr" && "${2:-}" == "create" ]]; then
    # Extract title from args
    TITLE=""
    BODY=""
    for i in "$@"; do
        if [[ "$i" == --title=* ]]; then
            TITLE="${i#--title=}"
        fi
    done
    echo "https://github.com/org/payments-service/pull/42" | tee -a "$LOG_FILE"
    echo "Pull request created successfully (stub)."
    exit 0
fi

if [[ "${1:-}" == "auth" ]]; then
    echo "Logged in to github.com as agent-test" 
    exit 0
fi

echo "gh: command recorded: $*"
exit 0
GHEOF
chmod +x /usr/local/bin/gh

# ── 3. Verify the workspace is intact ──────────────────────────────────────
if [ ! -d "/workspace/payments-service" ]; then
    echo "ERROR: payments-service repo not found" >&2
    exit 1
fi

if [ ! -d "/workspace/transaction-validator-worktree" ]; then
    echo "ERROR: feature worktree not found" >&2
    exit 1
fi

# ── 4. Verify tests pass in the worktree (they must pass for a valid sandbox) ──
cd /workspace/transaction-validator-worktree
python3 -m pytest tests/ -q --tb=short 2>&1 | tail -5

echo ""
echo "=== Sandbox ready ==="
echo "Repo at:       /workspace/payments-service"
echo "Feature work:  /workspace/transaction-validator-worktree  (branch: feature/transaction-validator)"
echo "Base branch:   main"