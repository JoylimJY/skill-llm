#!/usr/bin/env python3
"""
Generate the sandbox workspace for the openclaw-config-rollback task.
Creates the full directory structure, realistic scripts, and distractor files.
"""

import os
import json
import stat
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

HOME = Path(os.path.expanduser("~"))
OPENCLAW_DIR = HOME / ".openclaw"

# === Directory structure ===
dirs = [
    OPENCLAW_DIR / "backups",
    OPENCLAW_DIR / "docs",
    OPENCLAW_DIR / "scripts",
    OPENCLAW_DIR / "workspace" / "skills" / "config-rollback" / "scripts",
    OPENCLAW_DIR / "workspace" / "skills" / "config-rollback" / "docs",
    OPENCLAW_DIR / "workspace" / "skills" / "brain2claw-content-manager" / "work" / "cases",
    OPENCLAW_DIR / "logs",
    OPENCLAW_DIR / "tmp",
    OPENCLAW_DIR / "workspace" / "plugins",
    OPENCLAW_DIR / "workspace" / "themes",
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# === Main openclaw.json (initial config, missing payment-processor) ===
openclaw_config = {
    "version": "2.1.4",
    "gateway": {
        "port": 8742,
        "host": "localhost",
        "timeout": 30,
        "log_level": "info"
    },
    "skills": {
        "enabled": [
            "obsidian-sync",
            "discord-notifier",
            "task-scheduler"
        ],
        "disabled": [
            "payment-processor",
            "legacy-importer"
        ]
    },
    "features": {
        "auto_restart": True,
        "health_check_interval": 60
    }
}

with open(OPENCLAW_DIR / "openclaw.json", "w") as f:
    json.dump(openclaw_config, f, indent=2)

# === prepare-config-change.sh (the real script) ===
prepare_script = r"""#!/usr/bin/env bash
# prepare-config-change.sh - Prepare for a config modification with backup and state tracking
set -euo pipefail

OPENCLAW_DIR="$HOME/.openclaw"
BACKUP_DIR="$OPENCLAW_DIR/backups"
STATE_FILE="$OPENCLAW_DIR/.config-modified-state"
PENDING_FILE="$OPENCLAW_DIR/docs/PENDING_VERIFICATION.md"
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"

DESCRIPTION="${1:-}"
VERIFICATION_ITEMS="${2:-}"

if [ -z "$DESCRIPTION" ]; then
    echo "ERROR: Description is required." >&2
    echo "Usage: $0 \"description\" \"item1,item2\"" >&2
    exit 1
fi

# Create backup with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/openclaw_${TIMESTAMP}.json"
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# Calculate rollback deadline (5 minutes from now)
DEADLINE=$(date -d "+5 minutes" +%s 2>/dev/null || date -v+5M +%s)
DEADLINE_HUMAN=$(date -d "@$DEADLINE" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || date -r "$DEADLINE" "+%Y-%m-%d %H:%M:%S")

# Write state file
cat > "$STATE_FILE" <<EOF
DESCRIPTION=$DESCRIPTION
BACKUP_FILE=$BACKUP_FILE
DEADLINE=$DEADLINE
DEADLINE_HUMAN=$DEADLINE_HUMAN
TIMESTAMP=$TIMESTAMP
EOF

echo "⏰ Rollback deadline: $DEADLINE_HUMAN (5 minutes)"

# Update PENDING_VERIFICATION.md
mkdir -p "$(dirname "$PENDING_FILE")"
cat >> "$PENDING_FILE" <<EOF

## Change: $DESCRIPTION
**Time:** $(date "+%Y-%m-%d %H:%M:%S")
**Backup:** $BACKUP_FILE
**Deadline:** $DEADLINE_HUMAN

### Verification Items:
EOF

if [ -n "$VERIFICATION_ITEMS" ]; then
    IFS=',' read -ra ITEMS <<< "$VERIFICATION_ITEMS"
    for item in "${ITEMS[@]}"; do
        item=$(echo "$item" | sed 's/^[[:space:]]*//')
        echo "- [ ] $item" >> "$PENDING_FILE"
    done
else
    echo "- [ ] General verification" >> "$PENDING_FILE"
fi

echo "" >> "$PENDING_FILE"
echo "---" >> "$PENDING_FILE"

echo ""
echo "📋 Next steps:"
echo "  1. Edit ~/.openclaw/openclaw.json"
echo "  2. Restart Gateway within 5 minutes"
echo "  3. Verify: $VERIFICATION_ITEMS"
"""

prepare_path = OPENCLAW_DIR / "scripts" / "prepare-config-change.sh"
with open(prepare_path, "w") as f:
    f.write(prepare_script)
os.chmod(prepare_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# Also place in workspace location
workspace_prepare = OPENCLAW_DIR / "workspace" / "skills" / "config-rollback" / "scripts" / "prepare-config-change.sh"
with open(workspace_prepare, "w") as f:
    f.write(prepare_script)
os.chmod(workspace_prepare, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# === rollback-guardian.sh ===
guardian_script = r"""#!/usr/bin/env bash
# rollback-guardian.sh - Timeout rollback guardian daemon
set -euo pipefail

OPENCLAW_DIR="$HOME/.openclaw"
STATE_FILE="$OPENCLAW_DIR/.config-modified-state"
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"
LOG_FILE="$OPENCLAW_DIR/logs/rollback-guardian.log"

mkdir -p "$(dirname "$LOG_FILE")"

# No state file = no pending change, exit quietly
if [ ! -f "$STATE_FILE" ]; then
    exit 0
fi

source "$STATE_FILE"
NOW=$(date +%s)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Check if gateway is running (simplified check)
GATEWAY_RUNNING=false
if pgrep -f "openclaw-gateway" > /dev/null 2>&1; then
    GATEWAY_RUNNING=true
fi

if [ "$GATEWAY_RUNNING" = "true" ]; then
    log "Gateway running. Clearing state (change accepted)."
    rm -f "$STATE_FILE"
    exit 0
fi

if [ "$NOW" -lt "$DEADLINE" ]; then
    REMAINING=$((DEADLINE - NOW))
    log "Gateway not running. Waiting... ${REMAINING}s remaining until rollback."
    exit 0
fi

# Timeout reached - perform rollback
log "TIMEOUT REACHED. Performing automatic rollback from $BACKUP_FILE"
if [ -f "$BACKUP_FILE" ]; then
    cp "$BACKUP_FILE" "$CONFIG_FILE"
    log "Rollback complete. Config restored from $BACKUP_FILE"
else
    log "ERROR: Backup file not found: $BACKUP_FILE"
fi

rm -f "$STATE_FILE"
log "State file cleared after rollback."
"""

guardian_path = OPENCLAW_DIR / "scripts" / "rollback-guardian.sh"
with open(guardian_path, "w") as f:
    f.write(guardian_script)
os.chmod(guardian_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

workspace_guardian = OPENCLAW_DIR / "workspace" / "skills" / "config-rollback" / "scripts" / "rollback-guardian.sh"
with open(workspace_guardian, "w") as f:
    f.write(guardian_script)
os.chmod(workspace_guardian, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# === config-alias.sh ===
alias_script = r"""#!/usr/bin/env bash
# config-alias.sh - Interactive config assistant
echo "OpenClaw Config Assistant"
echo "Available commands:"
echo "  prepare  - Prepare config change"
echo "  rollback - Manual rollback"
echo "  status   - Show current state"
"""

alias_path = OPENCLAW_DIR / "scripts" / "config-alias.sh"
with open(alias_path, "w") as f:
    f.write(alias_script)
os.chmod(alias_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)

workspace_alias = OPENCLAW_DIR / "workspace" / "skills" / "config-rollback" / "scripts" / "config-alias.sh"
with open(workspace_alias, "w") as f:
    f.write(alias_script)
os.chmod(workspace_alias, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)

# === PENDING_VERIFICATION.md (initial, empty template) ===
pending_md = """# Pending Verification Items

This document tracks verification tasks after configuration changes.

---
"""
with open(OPENCLAW_DIR / "docs" / "PENDING_VERIFICATION.md", "w") as f:
    f.write(pending_md)

# === CONFIG_QUICKREF.md ===
quickref = """# Config Quick Reference

## Common Config Paths
- Main config: ~/.openclaw/openclaw.json
- Backups: ~/.openclaw/backups/
- Scripts: ~/.openclaw/scripts/

## Gateway Commands
- Start: openclaw gateway start
- Stop: openclaw gateway stop
- Restart: openclaw gateway restart
- Status: openclaw gateway status
"""
with open(OPENCLAW_DIR / "docs" / "CONFIG_QUICKREF.md", "w") as f:
    f.write(quickref)

# === CONFIG_CHANGELOG.md ===
changelog = """# Config Changelog

## 2026-03-10 - Initial setup
- Configured gateway port 8742
- Enabled obsidian-sync skill

## 2026-03-14 - Added discord notifier
- Enabled discord-notifier skill
- Set log level to info
"""
with open(OPENCLAW_DIR / "docs" / "CONFIG_CHANGELOG.md", "w") as f:
    f.write(changelog)

# === Design case distractor ===
case_content = """# Case 001: Config Management Flow

## Overview
This case documents the standard config management flow for OpenClaw.

## Steps
1. Prepare change with backup
2. Edit config
3. Restart gateway
4. Verify functionality

## Notes
Always use prepare-config-change.sh before editing.
"""
with open(OPENCLAW_DIR / "workspace" / "skills" / "brain2claw-content-manager" / "work" / "cases" / "001-config-management-flow.md", "w") as f:
    f.write(case_content)

# === Old/distractor backup files (wrong format, should not be picked) ===
old_date = datetime(2026, 1, 15, 9, 30, 0)
old_backup = {
    "version": "2.0.1",
    "gateway": {"port": 8742, "host": "localhost"},
    "skills": {"enabled": ["obsidian-sync"]}
}
old_backup_path = OPENCLAW_DIR / "backups" / f"openclaw_{old_date.strftime('%Y%m%d_%H%M%S')}.json"
with open(old_backup_path, "w") as f:
    json.dump(old_backup, f, indent=2)

# Another distractor: a .bak file (wrong extension, should be ignored by scripts)
with open(OPENCLAW_DIR / "backups" / "openclaw_manual.bak", "w") as f:
    f.write('{"version": "old", "note": "manual backup, not part of rotation"}')

# === Distractor log files ===
log_entries = [
    "[2026-03-10 08:00:00] Gateway started on port 8742",
    "[2026-03-10 08:01:00] Skill obsidian-sync loaded",
    "[2026-03-14 14:22:00] Config change detected",
    "[2026-03-14 14:22:05] Backup created successfully",
    "[2026-03-14 14:27:00] Gateway restarted, state cleared",
]
with open(OPENCLAW_DIR / "logs" / "gateway.log", "w") as f:
    f.write("\n".join(log_entries) + "\n")

with open(OPENCLAW_DIR / "logs" / "rollback-guardian.log", "w") as f:
    f.write("[2026-03-14 14:22:00] No state file found. Exiting quietly.\n")

# === Distractor plugin/theme files ===
for plugin in ["auth-plugin", "rate-limiter", "cache-manager"]:
    plugin_dir = OPENCLAW_DIR / "workspace" / "plugins" / plugin
    plugin_dir.mkdir(parents=True, exist_ok=True)
    with open(plugin_dir / "plugin.json", "w") as f:
        json.dump({"name": plugin, "version": "1.0.0", "enabled": False}, f)

for theme in ["dark-mode", "compact-ui"]:
    theme_dir = OPENCLAW_DIR / "workspace" / "themes" / theme
    theme_dir.mkdir(parents=True, exist_ok=True)
    with open(theme_dir / "theme.css", "w") as f:
        f.write(f"/* {theme} theme */\n:root {{ --primary: #333; }}\n")

# === CONFIG_CHANGE_RULES.md in workspace root ===
rules_content = """# Config Change Rules

## Mandatory Steps
1. Always backup before changing
2. Document the reason for change
3. Test within 5 minutes of making change
4. If test fails, rollback immediately

## Rollback Procedure
See emergency rollback in SKILL.md documentation.

## Audit Requirements
All changes must be logged in CONFIG_CHANGELOG.md
"""
with open(OPENCLAW_DIR / "CONFIG_CHANGE_RULES.md", "w") as f:
    f.write(rules_content)

# === tmp distractor ===
with open(OPENCLAW_DIR / "tmp" / "last-operation.txt", "w") as f:
    f.write("prepare-config-change\n2026-03-14 14:21:58\nStatus: completed\n")

# === Skill metadata ===
skill_meta = {
    "name": "config-rollback",
    "version": "1.0.2",
    "author": "小麦",
    "description": "Config rollback management skill",
    "scripts": ["prepare-config-change.sh", "rollback-guardian.sh", "config-alias.sh"]
}
with open(OPENCLAW_DIR / "workspace" / "skills" / "config-rollback" / "skill.json", "w") as f:
    json.dump(skill_meta, f, indent=2)

print("✅ Sandbox workspace generated successfully.")
print(f"   OpenClaw dir: {OPENCLAW_DIR}")
print(f"   Config: {OPENCLAW_DIR / 'openclaw.json'}")
print(f"   Scripts: {OPENCLAW_DIR / 'scripts'}")