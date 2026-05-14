#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Install mock CLIs so they shadow real tools
cp "$WORKSPACE/scripts/mock-gh.sh"       /usr/local/bin/gh
cp "$WORKSPACE/scripts/mock-clawhub.sh"  /usr/local/bin/clawhub
chmod +x /usr/local/bin/gh
chmod +x /usr/local/bin/clawhub

# Make all workspace scripts executable
find "$WORKSPACE/scripts" -name "*.sh" -exec chmod +x {} \;

# Set up global git config to avoid identity errors during git init/commit
git config --global user.email "agent@localhost"
git config --global user.name "SkillEngineer"
git config --global init.defaultBranch main

# Create log files so mock CLIs can always append
touch /tmp/gh_calls.log /tmp/clawhub_calls.log
mkdir -p /tmp/clawhub_publish

echo "Setup complete. Mock CLIs installed."
echo "  gh    -> /usr/local/bin/gh (mock)"
echo "  clawhub -> /usr/local/bin/clawhub (mock)"