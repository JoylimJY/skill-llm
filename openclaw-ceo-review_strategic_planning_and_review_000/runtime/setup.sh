#!/bin/bash
set -e

cd /workspace

# Ensure git is properly configured
git config user.email "test@example.com"
git config user.name "TestUser"

# Make the .context directory visible
ls -la .context/ 2>/dev/null && echo ".context dir ready" || echo "WARNING: .context dir missing"

# Verify CLAUDE.md and TODOS.md exist
[ -f CLAUDE.md ] && echo "CLAUDE.md present" || echo "WARNING: CLAUDE.md missing"
[ -f TODOS.md ] && echo "TODOS.md present" || echo "WARNING: TODOS.md missing"

echo "Setup complete. Workspace ready for agent."