#!/usr/bin/env bash
set -euo pipefail

BASE=/root/.openclaw/workspace

# Make scripts executable
chmod +x "$BASE/scripts/nightly_optimizer.py"
chmod +x "$BASE/scripts/decision_logger.py"

# Ensure MEMORY/DECISIONS exists and is writable
mkdir -p "$BASE/MEMORY/DECISIONS"

# Ensure sys.path will find decision_logger when optimizer runs
# (Both live in scripts/ so running from that directory works;
#  but we add a .pth so Python always finds it regardless of CWD)
SITE_PKG=$(python3 -c "import site; print(site.getsitepackages()[0])")
echo "$BASE/scripts" > "$SITE_PKG/openclaw_scripts.pth"

echo "Setup complete."