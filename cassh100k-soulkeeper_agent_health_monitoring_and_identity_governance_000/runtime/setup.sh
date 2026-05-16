#!/bin/bash
set -e

WORKSPACE=/root/.openclaw/workspace
SKILLS_DIR="$WORKSPACE/skills/soulkeeper"

# Make scripts executable
chmod +x "$SKILLS_DIR/audit.py"
chmod +x "$SKILLS_DIR/drift.py"
chmod +x "$SKILLS_DIR/remind.py"

# Symlink to PATH
ln -sf "$SKILLS_DIR/audit.py" /usr/local/bin/soul-audit
ln -sf "$SKILLS_DIR/drift.py" /usr/local/bin/soul-drift
ln -sf "$SKILLS_DIR/remind.py" /usr/local/bin/soul-remind

echo "[setup] SoulKeeper environment ready."
echo "[setup] Scripts available: soul-audit, soul-drift, soul-remind"
echo "[setup] Workspace: $WORKSPACE"