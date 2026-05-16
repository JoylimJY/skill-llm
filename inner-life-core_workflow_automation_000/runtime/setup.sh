#!/usr/bin/env bash
set -e

WORKSPACE="/workspace"
SKILL_REPO="https://github.com/DKistenev/openclaw-inner-life.git"
SKILL_DIR="$WORKSPACE/skills/inner-life-core"

echo "=== Cloning inner-life-core skill from GitHub ==="
# Clone into a temp location, then move the relevant skill subtree
TMPDIR=$(mktemp -d)
git clone --depth=1 "$SKILL_REPO" "$TMPDIR/openclaw-inner-life" 2>&1 || {
    echo "ERROR: Failed to clone $SKILL_REPO"
    exit 1
}

# Copy the skill directory into workspace/skills/inner-life-core
mkdir -p "$SKILL_DIR"
cp -r "$TMPDIR/openclaw-inner-life/skills/inner-life-core/"* "$SKILL_DIR/"
# Also copy the BRAIN.md and SELF.md if at repo root
cp "$TMPDIR/openclaw-inner-life/BRAIN.md" "$WORKSPACE/BRAIN.md" 2>/dev/null || true
cp "$TMPDIR/openclaw-inner-life/SELF.md" "$WORKSPACE/SELF.md" 2>/dev/null || true

rm -rf "$TMPDIR"

# Ensure skill scripts are executable
chmod +x "$SKILL_DIR/scripts/"*.sh 2>/dev/null || true

echo "=== Skill installed at $SKILL_DIR ==="
ls -la "$SKILL_DIR/scripts/" 2>/dev/null || echo "(no scripts dir found)"

# Verify jq is available
jq --version

echo "=== Setup complete ==="