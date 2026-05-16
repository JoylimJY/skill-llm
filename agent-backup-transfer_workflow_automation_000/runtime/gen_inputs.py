#!/usr/bin/env python3
"""
Generate sandbox workspace for the openclaw-backup skill evaluation.
Sets up:
  - ~/.openclaw/workspace/ with realistic nested structure
  - skills/openclaw-backup/openclaw-backup.sh (the real backup script)
  - 10 pre-existing fake backups in ~/openclaw-backups/
  - Distractor files throughout
"""

import os
import sys
import json
import tarfile
import io
import random
import time
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

HOME = Path(os.path.expanduser("~"))
WORKSPACE = HOME / ".openclaw" / "workspace"
BACKUPS_DIR = HOME / "openclaw-backups"
SKILLS_DIR = WORKSPACE / "skills" / "openclaw-backup"
HOOKS_DIR = WORKSPACE / ".hooks"

# --- Create directory structure ---
for d in [WORKSPACE, BACKUPS_DIR, SKILLS_DIR, HOOKS_DIR,
          WORKSPACE / "memories",
          WORKSPACE / "memories" / "episodic",
          WORKSPACE / "memories" / "semantic",
          WORKSPACE / "sessions",
          WORKSPACE / "agents" / "primary",
          WORKSPACE / "agents" / "secondary",
          WORKSPACE / "config",
          WORKSPACE / "logs",
          WORKSPACE / "temp",
          WORKSPACE / "node_modules" / "some-dep",
          WORKSPACE / ".git" / "objects",
          HOME / ".openclaw" / "sessions",
          HOME / ".openclaw" / "config",
          ]:
    d.mkdir(parents=True, exist_ok=True)

# --- Core workspace files (these MUST appear in the backup) ---
identity = {
    "name": "Axiom",
    "version": "2.3.1",
    "created": "2024-01-15T08:00:00Z",
    "personality": "analytical",
    "domain": "industrial_ops"
}
(WORKSPACE / "identity.json").write_text(json.dumps(identity, indent=2))

core_memories = {
    "facts": [
        "I am Axiom, deployed for industrial operations monitoring.",
        "Primary goal: anomaly detection in sensor networks.",
        "User: Dr. Chen Wei, Lead Systems Engineer."
    ],
    "last_updated": "2025-06-01T12:34:56Z"
}
(WORKSPACE / "memories" / "core.json").write_text(json.dumps(core_memories, indent=2))

(WORKSPACE / "memories" / "episodic" / "session_001.json").write_text(json.dumps({
    "session_id": "s001",
    "events": ["Analyzed pump sensor anomaly on 2025-05-30", "Generated report #42"]
}))
(WORKSPACE / "memories" / "semantic" / "domain_knowledge.json").write_text(json.dumps({
    "domain": "industrial_ops",
    "concepts": ["PID control", "SCADA", "vibration analysis"]
}))

(WORKSPACE / "agents" / "primary" / "agent.json").write_text(json.dumps({
    "id": "primary-001",
    "status": "active",
    "capabilities": ["monitoring", "reporting", "alerting"]
}))
(WORKSPACE / "agents" / "secondary" / "agent.json").write_text(json.dumps({
    "id": "secondary-002",
    "status": "standby"
}))

(WORKSPACE / "config" / "settings.json").write_text(json.dumps({
    "gateway_port": 18789,
    "log_level": "info",
    "auto_backup": False
}))

(WORKSPACE / "sessions" / "latest.json").write_text(json.dumps({
    "session_id": "s_latest",
    "start": "2025-06-10T09:00:00Z"
}))

# --- Files that MUST be excluded from backup ---
(WORKSPACE / "logs" / "gateway.log").write_text("2025-06-10 09:00:01 INFO Gateway started\n" * 100)
(WORKSPACE / "logs" / "error.log").write_text("2025-06-10 09:05:00 ERROR Timeout on sensor 7\n" * 50)
(WORKSPACE / "temp" / "scratch.tmp").write_text("temporary processing data - do not backup")
(WORKSPACE / "temp" / "cache.bin").write_bytes(bytes(random.getrandbits(8) for _ in range(1024)))
(WORKSPACE / "node_modules" / "some-dep" / "index.js").write_text("module.exports = {};")
(WORKSPACE / ".git" / "objects" / "abc123").write_bytes(b"\x00\x01\x02\x03")

# --- Distractor files in ~/.openclaw/ (root config) ---
(HOME / ".openclaw" / "config" / "global.json").write_text(json.dumps({"theme": "dark", "lang": "en"}))
(HOME / ".openclaw" / "sessions" / "web_session.dat").write_text("session_token=FAKE12345")
(HOME / ".openclaw" / "VERSION").write_text("2.3.1\n")

# --- More distractor files ---
(HOME / "README_IGNORE.txt").write_text("This file is not relevant to the task.")
(HOME / "Downloads" / "old_report.pdf").write_bytes(b"%PDF-1.4 fake content") if (HOME / "Downloads").mkdir(exist_ok=True) or True else None
(HOME / "Documents").mkdir(exist_ok=True)
(HOME / "Documents" / "notes.txt").write_text("Meeting notes - Q2 review")

# -------------------------------------------------------
# THE REAL openclaw-backup.sh script
# -------------------------------------------------------
BACKUP_SCRIPT = r'''#!/bin/bash
# openclaw-backup.sh - Backup and restore OpenClaw agent workspace

BACKUP_DIR="$HOME/openclaw-backups"
WORKSPACE_DIR="$HOME/.openclaw/workspace"
OPENCLAW_DIR="$HOME/.openclaw"
MAX_BACKUPS=10
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
BACKUP_NAME="openclaw-backup-${TIMESTAMP}.tar.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

mkdir -p "$BACKUP_DIR"

cmd_create() {
    echo "[openclaw-backup] Creating backup: $BACKUP_NAME"
    tar -czf "$BACKUP_PATH" \
        --exclude="$WORKSPACE_DIR/logs" \
        --exclude="$WORKSPACE_DIR/temp" \
        --exclude="$WORKSPACE_DIR/node_modules" \
        --exclude="$WORKSPACE_DIR/.git" \
        -C "$HOME" \
        .openclaw/
    echo "[openclaw-backup] Backup saved: $BACKUP_PATH"
    prune_old_backups
}

prune_old_backups() {
    local count
    count=$(ls -1 "$BACKUP_DIR"/openclaw-backup-*.tar.gz 2>/dev/null | wc -l)
    if [ "$count" -gt "$MAX_BACKUPS" ]; then
        echo "[openclaw-backup] Pruning old backups (keeping last $MAX_BACKUPS)..."
        ls -1t "$BACKUP_DIR"/openclaw-backup-*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f
        echo "[openclaw-backup] Pruning complete."
    fi
}

cmd_list() {
    echo "[openclaw-backup] Available backups in $BACKUP_DIR:"
    ls -1t "$BACKUP_DIR"/openclaw-backup-*.tar.gz 2>/dev/null || echo "  (none found)"
}

cmd_restore() {
    local src="$1"
    if [ -z "$src" ]; then
        echo "[openclaw-backup] ERROR: No backup file specified."
        exit 1
    fi
    if [ ! -f "$src" ]; then
        echo "[openclaw-backup] ERROR: File not found: $src"
        exit 1
    fi
    echo "[openclaw-backup] Restoring from: $src"
    tar -xzf "$src" -C "$HOME"
    echo "[openclaw-backup] Restore complete."
}

cmd_setup_auto() {
    local hook_dir="$WORKSPACE_DIR/.hooks"
    mkdir -p "$hook_dir"
    cat > "$hook_dir/post-memory-save.sh" <<'HOOKEOF'
#!/bin/bash
# Auto-backup hook: triggered after important memory saves
cd "$HOME/.openclaw/workspace"
./skills/openclaw-backup/openclaw-backup.sh create
HOOKEOF
    chmod +x "$hook_dir/post-memory-save.sh"
    echo "[openclaw-backup] Auto-backup hook created at: $hook_dir/post-memory-save.sh"
}

case "$1" in
    create)       cmd_create ;;
    list)         cmd_list ;;
    restore)      cmd_restore "$2" ;;
    setup-auto)   cmd_setup_auto ;;
    *)
        echo "Usage: $0 {create|list|restore <file>|setup-auto}"
        exit 1
        ;;
esac
'''

(SKILLS_DIR / "openclaw-backup.sh").write_text(BACKUP_SCRIPT)

# -------------------------------------------------------
# Create 10 pre-existing fake backups (oldest to newest)
# We want the OLDEST one (lowest timestamp) to get pruned
# when the agent creates backup #11
# -------------------------------------------------------
base_time = datetime(2025, 1, 1, 2, 0, 0)

fake_backup_names = []
for i in range(10):
    ts = base_time + timedelta(days=i * 7)  # weekly backups
    name = f"openclaw-backup-{ts.strftime('%Y-%m-%d_%H%M%S')}.tar.gz"
    fake_backup_names.append(name)
    backup_path = BACKUPS_DIR / name

    # Create a minimal valid tarball
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tf:
        # Add a fake identity file inside
        content = json.dumps({"name": f"FakeAgent-v{i}", "backup_index": i}).encode()
        info = tarfile.TarInfo(name=".openclaw/workspace/identity.json")
        info.size = len(content)
        tf.addfile(info, io.BytesIO(content))
    buf.seek(0)
    backup_path.write_bytes(buf.getvalue())

    # Set modification time to simulate age
    mtime = ts.timestamp()
    os.utime(backup_path, (mtime, mtime))

# Record the OLDEST backup name for eval
oldest_backup = fake_backup_names[0]
(HOME / ".eval_oldest_backup.txt").write_text(oldest_backup)

# Record ALL pre-seeded backup names for eval
(HOME / ".eval_preseeded_backups.json").write_text(json.dumps(fake_backup_names))

print(f"[gen_inputs] Workspace created at {WORKSPACE}")
print(f"[gen_inputs] {len(fake_backup_names)} pre-existing backups created in {BACKUPS_DIR}")
print(f"[gen_inputs] Oldest backup (should be pruned): {oldest_backup}")
print(f"[gen_inputs] openclaw-backup.sh installed at {SKILLS_DIR / 'openclaw-backup.sh'}")