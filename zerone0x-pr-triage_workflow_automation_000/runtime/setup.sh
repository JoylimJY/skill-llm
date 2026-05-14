#!/bin/bash
set -e

WORKSPACE="/workspace"

# Make mock gh binary executable and put it first in PATH
chmod +x "$WORKSPACE/gh"

# Create a wrapper so 'gh' resolves to our mock regardless of env -u GH_TOKEN usage
# The skill requires: env -u GH_TOKEN -u GITHUB_TOKEN gh <command>
# env -u strips variables but uses the same PATH, so our /workspace/gh will be found
# if /workspace is first in PATH.

# Prepend /workspace to PATH system-wide
echo 'export PATH="/workspace:$PATH"' >> /etc/bash.bashrc
echo 'export PATH="/workspace:$PATH"' >> /etc/profile

# Also set it for this session and create a /usr/local/bin symlink as fallback
ln -sf "$WORKSPACE/gh" /usr/local/bin/gh

# Verify mock works
export PATH="/workspace:$PATH"
result=$(gh pr list --repo dataflow-org/etl-pipeline --state open --limit 500 --json number,title 2>/dev/null)
count=$(echo "$result" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
echo "Mock gh returns $count PRs - setup OK"

# Set a fake GH_TOKEN and GITHUB_TOKEN to verify env -u stripping in agent
export GH_TOKEN="fake_token_should_be_stripped"
export GITHUB_TOKEN="fake_token_should_be_stripped"

echo "Setup complete. Mock gh is ready at /workspace/gh and /usr/local/bin/gh"
echo "PATH=$PATH"