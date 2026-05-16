#!/bin/bash
set -e

# Find the globally installed wip-file-guard package and locate guard.mjs
GUARD_PATH=$(node -e "require.resolve('@wipcomputer/wip-file-guard/guard.mjs')" 2>/dev/null || true)

if [ -z "$GUARD_PATH" ]; then
    # Try to find it in the npm global prefix
    NPM_PREFIX=$(npm root -g)
    GUARD_PATH="$NPM_PREFIX/@wipcomputer/wip-file-guard/guard.mjs"
fi

if [ ! -f "$GUARD_PATH" ]; then
    # fallback: search
    GUARD_PATH=$(find /usr -name "guard.mjs" 2>/dev/null | grep "wip-file-guard" | head -1)
fi

echo "Found guard.mjs at: $GUARD_PATH"

# Create a symlink in /workspace for easy access
if [ -f "$GUARD_PATH" ]; then
    ln -sf "$GUARD_PATH" /workspace/guard.mjs
    echo "Symlinked guard.mjs to /workspace/guard.mjs"
else
    echo "WARNING: guard.mjs not found via symlink, agent must locate it"
fi

# Ensure the workspace task spec is readable
chmod 644 /workspace/task_spec.json

# Verify node is available
node --version
npm --version

echo "Setup complete. Workspace ready at /workspace"