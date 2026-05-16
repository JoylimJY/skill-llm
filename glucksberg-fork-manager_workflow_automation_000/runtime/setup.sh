#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"
SKILL_DIR="$WORKSPACE/skills/fork-manager"

echo "=== Fork Manager Test Environment Setup ==="

# ── 1. Write full SKILL.md content ──
# The SKILL.md is provided by the benchmark orchestrator; we assume it's already
# at the expected location. If the gen_inputs_script created a placeholder, we leave it —
# the agent is expected to have access to the real SKILL.md through its tool invocation.
# We just ensure the file is not empty.
if [ ! -s "$SKILL_DIR/SKILL.md" ] || grep -q "content will be injected" "$SKILL_DIR/SKILL.md"; then
    echo "WARNING: SKILL.md is a placeholder. Agent will need the real skill content."
fi

# ── 2. Make mock gh executable and place on PATH ──
chmod +x "$SKILL_DIR/gh"

# Create a wrapper that routes to mock when called for the test repo
cat > /usr/local/bin/gh << 'GHEOF'
#!/usr/bin/env bash
# Mock gh wrapper for fork-manager testing
exec python3 /workspace/skills/fork-manager/gh "$@"
GHEOF
chmod +x /usr/local/bin/gh

# ── 3. Verify git repos are accessible ──
WORK_DIR="$WORKSPACE/repos/numcore-local"

if [ -d "$WORK_DIR/.git" ]; then
    echo "Working directory OK: $WORK_DIR"
    cd "$WORK_DIR"
    git remote -v
    git log --oneline -3
    git branch -a | head -20
else
    echo "ERROR: Working directory not found at $WORK_DIR"
    exit 1
fi

# ── 4. Ensure upstream has diverged from origin/main ──
cd "$WORK_DIR"
git fetch upstream 2>/dev/null || true
git fetch origin 2>/dev/null || true

UPSTREAM_AHEAD=$(git rev-list --count origin/main..upstream/main 2>/dev/null || echo "0")
echo "Upstream is $UPSTREAM_AHEAD commits ahead of origin/main"
if [ "$UPSTREAM_AHEAD" -lt 1 ]; then
    echo "ERROR: Upstream should be ahead of origin/main"
    exit 1
fi

# ── 5. Verify PR branches exist on origin ──
for branch in "fix/sparse-solver" "feat/gpu-backend" "fix/memory-leak" "local/precision-fix"; do
    if git ls-remote --exit-code origin "$branch" > /dev/null 2>&1; then
        echo "OK: origin/$branch exists"
    else
        echo "ERROR: origin/$branch missing"
        exit 1
    fi
done

# ── 6. Ensure config.json is valid ──
CONFIG="$SKILL_DIR/repos/numcore/config.json"
if [ -f "$CONFIG" ]; then
    python3 -c "import json; d=json.load(open('$CONFIG')); assert 101 in d['openPRs']; assert 102 in d['openPRs']; print('Config OK')"
else
    echo "ERROR: config.json missing"
    exit 1
fi

# ── 7. Set git config in working dir ──
cd "$WORK_DIR"
git config user.email "agent@test.local"
git config user.name "Test Agent"

echo ""
echo "=== Setup Complete ==="
echo "Skill dir: $SKILL_DIR"
echo "Working dir: $WORK_DIR"
echo "Config: $CONFIG"
echo ""
echo "Scenario:"
echo "  - PR #101 (fix/sparse-solver): OPEN — should stay in openPRs"
echo "  - PR #102 (feat/gpu-backend): CLOSED — agent must move to localPatches"
echo "  - PR #103 (fix/memory-leak): OPEN (was in droppedPatches) — agent must restore to openPRs"
echo "  - local/precision-fix: existing local patch"
echo "  - Upstream is 2 commits ahead — agent must sync main"
echo ""
echo "Task: Full sync of the numcore fork including PR state handling and production branch rebuild."