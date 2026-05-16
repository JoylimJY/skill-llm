#!/bin/bash
set -e

# ─────────────────────────────────────────────
# Create the actual sync.sh script at the exact path specified in SKILL.md
# ─────────────────────────────────────────────
mkdir -p /root/.openclaw/workspace/skills/obsidian-folder-sync/scripts
mkdir -p /root/.openclaw/workspace/logs

cat > /root/.openclaw/workspace/skills/obsidian-folder-sync/scripts/sync.sh << 'SYNCSCRIPT'
#!/bin/bash

# obsidian-folder-sync/scripts/sync.sh
# Usage: sync.sh <source_dir> <target_vault> [target_subdir]

set -euo pipefail

SOURCE_DIR="${1:-}"
TARGET_VAULT="${2:-}"
TARGET_SUBDIR="${3:-}"

LOG_FILE="${OBSIDIAN_SYNC_LOG:-$HOME/.openclaw/workspace/logs/obsidian-folder-sync.log}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

if [[ -z "$SOURCE_DIR" || -z "$TARGET_VAULT" ]]; then
    echo "Usage: $0 <source_dir> <target_vault> [target_subdir]"
    exit 1
fi

SOURCE_DIR="$(realpath "$SOURCE_DIR")"
TARGET_VAULT="$(realpath "$TARGET_VAULT")"

if [[ -z "$TARGET_SUBDIR" ]]; then
    TARGET_SUBDIR="$(basename "$SOURCE_DIR")"
fi

TARGET_DIR="$TARGET_VAULT/$TARGET_SUBDIR"

log "Starting sync: $SOURCE_DIR -> $TARGET_DIR"

mkdir -p "$TARGET_DIR"

# Create temp dir for file list
TMP_DIR="/tmp/obsidian-folder-sync-$$"
mkdir -p "$TMP_DIR"
FILE_LIST="$TMP_DIR/files.txt"

# Find all .md files, excluding banned directories
find "$SOURCE_DIR" -type f -name "*.md" \
    ! -path "*/node_modules/*" \
    ! -path "*/__pycache__/*" \
    ! -path "*/.git/*" \
    ! -path "*/.venv/*" \
    ! -path "*/.clawhub/*" \
    ! -path "*/.learnings/*" \
    | sed "s|^$SOURCE_DIR/||" \
    > "$FILE_LIST"

FILE_COUNT=$(wc -l < "$FILE_LIST")
log "Found $FILE_COUNT .md files to sync (excluding node_modules, __pycache__, .git, .venv, .clawhub, .learnings)"

# Perform rsync using --files-from
rsync -av --files-from="$FILE_LIST" "$SOURCE_DIR/" "$TARGET_DIR/"

log "Sync complete: $FILE_COUNT files synced to $TARGET_DIR"

# Cleanup temp dir
rm -rf "$TMP_DIR"
log "Cleaned up temp dir $TMP_DIR"
SYNCSCRIPT

chmod +x /root/.openclaw/workspace/skills/obsidian-folder-sync/scripts/sync.sh

echo "sync.sh installed at /root/.openclaw/workspace/skills/obsidian-folder-sync/scripts/sync.sh"
echo "Vault and source directories:"
ls /workspace/