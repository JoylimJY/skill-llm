#!/bin/bash
set -e

echo "=== Runtime Setup ==="

# Ensure git is configured
git config --global user.email "test@test.com" || true
git config --global user.name "Test" || true
git config --global init.defaultBranch main || true

# Allow git to access the mock repos directory
git config --global safe.directory '*' || true

# Verify reskill is installed
if which reskill > /dev/null 2>&1; then
    echo "reskill found at: $(which reskill)"
    reskill --version || true
else
    echo "WARNING: reskill not found globally, agent will need to use npx"
fi

# Verify the mock repos exist
echo "Mock skill repos:"
ls -la /opt/mock-skill-repos/ || echo "WARNING: Mock repos not found!"

# Test that the repos are valid git repos
for repo in /opt/mock-skill-repos/*.git; do
    echo "Checking repo: $repo"
    git ls-remote "file://$repo" HEAD || echo "WARNING: Cannot access $repo"
done

# Ensure workspace is set up
ls -la /workspace/

echo "=== Setup Complete ==="