#!/bin/bash
set -e

# Configure git globally for the container session
git config --global user.email "agent@test.local"
git config --global user.name "Test Agent"
git config --global init.defaultBranch main

# Create a fake 'gh' CLI that logs its invocation and simulates success
cat > /usr/local/bin/gh << 'GHEOF'
#!/bin/bash
# Mock GitHub CLI for sandbox testing
LOG="/workspace/gh_invocations.log"
echo "gh called with args: $@" >> "$LOG"
if [[ "$1" == "pr" && "$2" == "create" ]]; then
    echo "https://github.com/mock-org/infusion-firmware/pull/42"
    echo "PR created (mock): $@" >> "$LOG"
    exit 0
fi
echo "gh mock: unhandled command $@" >> "$LOG"
exit 0
GHEOF
chmod +x /usr/local/bin/gh

# Ensure pytest is callable
which pytest || pip3 install pytest -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

# Verify the workspace structure is intact
echo "=== Worktree list ==="
git -C /workspace/infusion-firmware worktree list

echo "=== Branch list ==="
git -C /workspace/infusion-firmware branch -a

echo "=== Feature branch commits ==="
git -C /workspace/infusion-firmware log --oneline feature/dose-calculation

echo "Setup complete. Agent should work from /workspace/worktrees/dose-calculation-wt"