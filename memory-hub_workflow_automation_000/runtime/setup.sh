#!/bin/bash
set -e

# Ensure git global config is present in the container runtime
git config --global user.email "agent-devops@test.local"
git config --global user.name "agent-devops"

# Make sure the shared-memory dir's remote points to the bare repo correctly
BARE_REPO="$HOME/.openclaw/_bare_remote"
SHARED_MEM="$HOME/.openclaw/shared-memory"

if [ -d "$SHARED_MEM/.git" ]; then
    git -C "$SHARED_MEM" remote set-url origin "$BARE_REPO"
    echo "✅ Remote URL confirmed: $BARE_REPO"
fi

# Ensure config.json exists and is readable
CONFIG="$SHARED_MEM/config.json"
if [ -f "$CONFIG" ]; then
    echo "✅ config.json found:"
    cat "$CONFIG"
fi

echo "✅ Setup complete. Workspace ready for agent."