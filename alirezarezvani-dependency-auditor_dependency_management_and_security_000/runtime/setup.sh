#!/usr/bin/env bash
set -euo pipefail

# ── Locate the actual skill scripts. The skill places them under the skill directory.
# According to SKILL.md, scripts are at scripts/dep_scanner.py, scripts/license_checker.py, scripts/upgrade_planner.py
# We need to find them and make sure they're accessible from /workspace/scripts/

SKILL_SCRIPT_SEARCH_DIRS=(
    "/workspace/scripts"
    "/skills/engineering/dependency-auditor/scripts"
    "/root/skills/engineering/dependency-auditor/scripts"
    "/home/user/skills/engineering/dependency-auditor/scripts"
    "/opt/skills/engineering/dependency-auditor/scripts"
)

FOUND_DIR=""
for DIR in "${SKILL_SCRIPT_SEARCH_DIRS[@]}"; do
    if [ -f "$DIR/dep_scanner.py" ]; then
        FOUND_DIR="$DIR"
        break
    fi
done

if [ -z "$FOUND_DIR" ]; then
    # Try a broader find
    FOUND=$(find / -name "dep_scanner.py" -not -path "*/proc/*" 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        FOUND_DIR=$(dirname "$FOUND")
    fi
fi

if [ -z "$FOUND_DIR" ]; then
    echo "ERROR: Could not find dep_scanner.py. Skill scripts not found."
    exit 1
fi

echo "Found skill scripts at: $FOUND_DIR"

# ── Ensure /workspace/scripts/ has all three tools
mkdir -p /workspace/scripts

for SCRIPT in dep_scanner.py license_checker.py upgrade_planner.py; do
    if [ ! -f "/workspace/scripts/$SCRIPT" ] && [ -f "$FOUND_DIR/$SCRIPT" ]; then
        cp "$FOUND_DIR/$SCRIPT" "/workspace/scripts/$SCRIPT"
        echo "Copied $SCRIPT to /workspace/scripts/"
    elif [ -f "/workspace/scripts/$SCRIPT" ]; then
        echo "$SCRIPT already in /workspace/scripts/"
    else
        echo "WARNING: $SCRIPT not found!"
    fi
done

chmod +x /workspace/scripts/dep_scanner.py
chmod +x /workspace/scripts/license_checker.py
chmod +x /workspace/scripts/upgrade_planner.py

echo "Setup complete. Scripts available:"
ls -la /workspace/scripts/*.py

# Ensure reports dir exists
mkdir -p /workspace/reports