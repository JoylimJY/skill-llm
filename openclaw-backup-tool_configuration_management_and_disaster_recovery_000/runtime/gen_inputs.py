#!/usr/bin/env python3
import os
import json
import random
import pathlib
import time

random.seed(42)

WORKSPACE = "/workspace"

# Create the OpenClaw directory structure as described in SKILL.md
openclaw_base = pathlib.Path(os.path.expanduser("~/.openclaw"))

# Core config files that backup.sh tracks
core_config_dir = openclaw_base
core_config_dir.mkdir(parents=True, exist_ok=True)

# Create the workspace/skills directory for the backup scripts
skills_dir = openclaw_base / "workspace" / "skills" / "openclaw-backup" / "scripts"
skills_dir.mkdir(parents=True, exist_ok=True)

# Create the memory directory
memory_dir = openclaw_base / "memory"
memory_dir.mkdir(parents=True, exist_ok=True)

# Create the backups directory (where backup.sh stores backups)
backups_dir = openclaw_base / "backups"
backups_dir.mkdir(parents=True, exist_ok=True)

# ---- Create the core tracked config files ----

identity_content = """# IDENTITY
name: OpenClaw Gateway Agent
version: 2.1.0
role: edge-gateway-controller
region: us-west-2
"""
(core_config_dir / "IDENTITY.md").write_text(identity_content)

user_content = """# USER PROFILE
username: fieldops_engineer
organization: EdgeNet Solutions
tier: professional
last_active: 2024-01-15
"""
(core_config_dir / "USER.md").write_text(user_content)

memory_content = """# MEMORY
## Session Log
- 2024-01-10: Initial gateway deployment
- 2024-01-12: Port configuration reviewed
- 2024-01-15: Skill installation scheduled
"""
(core_config_dir / "MEMORY.md").write_text(memory_content)

soul_content = """# SOUL
## Core Directives
1. Protect configuration integrity
2. Always backup before modification
3. Validate changes before applying
"""
(core_config_dir / "SOUL.md").write_text(soul_content)

tools_content = """# TOOLS
## Available Tools
- backup.sh: Configuration backup utility
- restore.sh: Configuration restore utility
- restart.sh: Gateway restart utility
"""
(core_config_dir / "TOOLS.md").write_text(tools_content)

# The main config file the agent must modify then restore
openclaw_config = {
    "gateway_port": 8080,
    "gateway_host": "0.0.0.0",
    "log_level": "INFO",
    "max_connections": 100,
    "timeout_seconds": 30,
    "tls_enabled": False,
    "plugin_dir": "/opt/openclaw/plugins",
    "data_dir": "/var/openclaw/data",
    "admin_ui_enabled": True,
    "metrics_port": 9091
}
(core_config_dir / "openclaw.json").write_text(json.dumps(openclaw_config, indent=2))

# Memory sub-files
(memory_dir / "sessions.json").write_text(json.dumps({"sessions": [], "total": 0}))
(memory_dir / "cache.json").write_text(json.dumps({"cache_entries": 0, "last_flush": "2024-01-15T00:00:00Z"}))
(memory_dir / "events.log").write_text("2024-01-15T10:00:00Z [INFO] Gateway started\n2024-01-15T10:01:00Z [INFO] Config loaded\n")

# ---- Create the backup.sh script ----
backup_sh_content = r"""#!/bin/bash
# OpenClaw Backup Script
# Backs up core configuration files to a timestamped directory

OPENCLAW_HOME="$HOME/.openclaw"
BACKUP_ROOT="$OPENCLAW_HOME/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/memory"

echo "[backup.sh] Creating backup: $BACKUP_DIR"

# Backup core files
for f in IDENTITY.md USER.md MEMORY.md SOUL.md TOOLS.md openclaw.json; do
    if [ -f "$OPENCLAW_HOME/$f" ]; then
        cp "$OPENCLAW_HOME/$f" "$BACKUP_DIR/$f"
        echo "[backup.sh] Backed up: $f"
    fi
done

# Backup memory directory
if [ -d "$OPENCLAW_HOME/memory" ]; then
    cp -r "$OPENCLAW_HOME/memory/." "$BACKUP_DIR/memory/"
    echo "[backup.sh] Backed up: memory/"
fi

echo "[backup.sh] Backup complete -> $BACKUP_DIR"
echo "$BACKUP_DIR" > "$OPENCLAW_HOME/.last_backup_path"
"""
(skills_dir / "backup.sh").write_text(backup_sh_content)

# ---- Create the restore.sh script ----
restore_sh_content = r"""#!/bin/bash
# OpenClaw Restore Script
# Lists available backups and restores selected one

OPENCLAW_HOME="$HOME/.openclaw"
BACKUP_ROOT="$OPENCLAW_HOME/backups"

echo "[restore.sh] Available backups:"
echo "------------------------------"

mapfile -t BACKUPS < <(ls -1t "$BACKUP_ROOT" 2>/dev/null)

if [ ${#BACKUPS[@]} -eq 0 ]; then
    echo "[restore.sh] No backups found in $BACKUP_ROOT"
    exit 1
fi

for i in "${!BACKUPS[@]}"; do
    echo "  [$i] ${BACKUPS[$i]}"
done

echo "------------------------------"

# If argument provided, use it; otherwise prompt
if [ -n "$1" ]; then
    CHOICE="$1"
else
    read -p "Select backup number to restore [0 = most recent]: " CHOICE
fi

CHOICE=${CHOICE:-0}
SELECTED="${BACKUPS[$CHOICE]}"

if [ -z "$SELECTED" ]; then
    echo "[restore.sh] Invalid selection."
    exit 1
fi

RESTORE_FROM="$BACKUP_ROOT/$SELECTED"
echo "[restore.sh] Restoring from: $RESTORE_FROM"

# Restore core files
for f in IDENTITY.md USER.md MEMORY.md SOUL.md TOOLS.md openclaw.json; do
    if [ -f "$RESTORE_FROM/$f" ]; then
        cp "$RESTORE_FROM/$f" "$OPENCLAW_HOME/$f"
        echo "[restore.sh] Restored: $f"
    fi
done

# Restore memory directory
if [ -d "$RESTORE_FROM/memory" ]; then
    cp -r "$RESTORE_FROM/memory/." "$OPENCLAW_HOME/memory/"
    echo "[restore.sh] Restored: memory/"
fi

echo "[restore.sh] Restore complete from backup: $SELECTED"
echo "$SELECTED" > "$OPENCLAW_HOME/.last_restored_backup"
"""
(skills_dir / "restore.sh").write_text(restore_sh_content)

# ---- Create the restart.sh script ----
restart_sh_content = r"""#!/bin/bash
# OpenClaw Gateway Restart Script
echo "[restart.sh] Restarting OpenClaw Gateway..."
echo "[restart.sh] Gateway restarted successfully."
"""
(skills_dir / "restart.sh").write_text(restart_sh_content)

# ---- Create distractor files in workspace ----
workspace = pathlib.Path(WORKSPACE)

# Various distractor directories and files
distractors = [
    ("logs/gateway.log", "2024-01-15 startup sequence initiated\n2024-01-15 port binding: 8080\n"),
    ("logs/errors.log", ""),
    ("logs/access.log", "GET /api/status 200\nGET /api/config 200\n"),
    ("configs/network.yaml", "interface: eth0\nmtu: 1500\ndns: [8.8.8.8, 8.8.4.4]\n"),
    ("configs/firewall_rules.conf", "ALLOW 22/tcp\nALLOW 8080/tcp\nDENY ALL\n"),
    ("configs/ssl_certs.conf", "cert_path: /etc/ssl/certs/openclaw.crt\nkey_path: /etc/ssl/private/openclaw.key\n"),
    ("plugins/auth_plugin/manifest.json", json.dumps({"name": "auth", "version": "1.0", "enabled": True})),
    ("plugins/metrics_plugin/manifest.json", json.dumps({"name": "metrics", "version": "2.1", "enabled": True})),
    ("plugins/metrics_plugin/config.json", json.dumps({"interval_seconds": 60, "endpoint": "/metrics"})),
    ("data/telemetry/device_001.json", json.dumps({"device_id": "dev-001", "readings": [{"ts": 1705276800, "val": 23.5}]})),
    ("data/telemetry/device_002.json", json.dumps({"device_id": "dev-002", "readings": [{"ts": 1705276800, "val": 18.2}]})),
    ("data/exports/report_20240115.csv", "device_id,timestamp,value\ndev-001,2024-01-15,23.5\ndev-002,2024-01-15,18.2\n"),
    ("scripts/health_check.sh", "#!/bin/bash\ncurl -s http://localhost:8080/health\n"),
    ("scripts/deploy.sh", "#!/bin/bash\necho 'Deploying OpenClaw...'\n"),
    ("scripts/migrate_db.sh", "#!/bin/bash\necho 'Running migrations...'\n"),
    ("docs/architecture.md", "# Architecture\nOpenClaw uses a microservices architecture...\n"),
    ("docs/api_reference.md", "# API Reference\n## GET /api/status\nReturns gateway status.\n"),
    ("tmp/install_lock", "PID:12345\n"),
    ("tmp/pending_updates.json", json.dumps({"updates": ["plugin-auth-v1.1", "plugin-metrics-v2.2"]})),
]

for rel_path, content in distractors:
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# Also create a fake "old config" in workspace to confuse agents
(workspace / "configs" / "openclaw_backup_old.json").write_text(
    json.dumps({"gateway_port": 7070, "gateway_host": "127.0.0.1", "note": "this is NOT the active config"}, indent=2)
)

print("Workspace and OpenClaw environment initialized successfully.")
print(f"OpenClaw home: {openclaw_base}")
print(f"Active config: {core_config_dir / 'openclaw.json'}")
print(f"Backup scripts: {skills_dir}")