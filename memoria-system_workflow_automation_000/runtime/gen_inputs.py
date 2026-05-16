#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the Memoria System task.
Creates a realistic but broken/partial memoria-system installation
with distractor files and a corrupted memory structure.
"""
import os
import json
import stat
import random

random.seed(42)

WORKSPACE = "/workspace"
MEMORIA_DIR = os.path.join(WORKSPACE, "memoria-system")

# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────
def makedirs(*parts):
    path = os.path.join(*parts)
    os.makedirs(path, exist_ok=True)
    return path

def write_file(path, content, executable=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    if executable:
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ─────────────────────────────────────────────
# 1.  Shell scripts (realistic stubs that actually work)
# ─────────────────────────────────────────────

# memory-migrate.sh
migrate_sh = r'''#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.json"
MEMORY_BASE=$(jq -r '.memory.base_path' "$CONFIG" 2>/dev/null || echo "./memory")

# Resolve relative path
if [[ "$MEMORY_BASE" != /* ]]; then
    MEMORY_BASE="${SCRIPT_DIR}/${MEMORY_BASE}"
fi

cmd="${1:-}"
shift || true

case "$cmd" in
  init)
    echo "[migrate] Initializing memory structure at $MEMORY_BASE"
    mkdir -p "$MEMORY_BASE/semantic/knowledge"
    mkdir -p "$MEMORY_BASE/episodic/events"
    mkdir -p "$MEMORY_BASE/procedural/scripts"
    mkdir -p "$MEMORY_BASE/working/session"
    mkdir -p "$MEMORY_BASE/index/search"
    # Create stub files if missing
    [ -f "$MEMORY_BASE/semantic/facts.md" ]    || echo "# Facts"    > "$MEMORY_BASE/semantic/facts.md"
    [ -f "$MEMORY_BASE/semantic/concepts.md" ] || echo "# Concepts" > "$MEMORY_BASE/semantic/concepts.md"
    [ -f "$MEMORY_BASE/procedural/skills.md" ] || echo "# Skills"   > "$MEMORY_BASE/procedural/skills.md"
    [ -f "$MEMORY_BASE/procedural/workflows.md" ] || echo "# Workflows" > "$MEMORY_BASE/procedural/workflows.md"
    [ -f "$MEMORY_BASE/working/current.md" ]   || echo "# Current"  > "$MEMORY_BASE/working/current.md"
    if [ ! -f "$MEMORY_BASE/index/tags.json" ]; then
        echo '{"tags":{}}' > "$MEMORY_BASE/index/tags.json"
    fi
    if [ ! -f "$MEMORY_BASE/index/timeline.json" ]; then
        echo '{"events":[]}' > "$MEMORY_BASE/index/timeline.json"
    fi
    echo "[migrate] init complete."
    ;;
  daily)
    DATE="${1:-$(date +%Y-%m-%d)}"
    TARGET="$MEMORY_BASE/episodic/${DATE}.md"
    if [ -f "$TARGET" ]; then
        echo "[migrate] Daily file already exists: $TARGET"
    else
        echo "# Memory Log: $DATE" > "$TARGET"
        echo "" >> "$TARGET"
        echo "## Summary" >> "$TARGET"
        echo "" >> "$TARGET"
        echo "## Events" >> "$TARGET"
        echo "" >> "$TARGET"
        echo "[migrate] Created daily log: $TARGET"
    fi
    ;;
  migrate)
    VERSION="${1:-}"
    echo "[migrate] Migrating from version: ${VERSION:-unknown}"
    # Re-run init to ensure structure is up to date
    "$SCRIPT_DIR/memory-migrate.sh" init
    echo "[migrate] Migration complete."
    ;;
  *)
    echo "Usage: $0 {init|daily [DATE]|migrate [VERSION]}" >&2
    exit 1
    ;;
esac
'''

# memory-health-check.sh
health_sh = r'''#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.json"
MEMORY_BASE=$(jq -r '.memory.base_path' "$CONFIG" 2>/dev/null || echo "./memory")

if [[ "$MEMORY_BASE" != /* ]]; then
    MEMORY_BASE="${SCRIPT_DIR}/${MEMORY_BASE}"
fi

FIX=false
OVERRIDE_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --fix)  FIX=true; shift ;;
        --path) OVERRIDE_PATH="$2"; shift 2 ;;
        *)      echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

[[ -n "$OVERRIDE_PATH" ]] && MEMORY_BASE="$OVERRIDE_PATH"

echo "[health] Checking memory structure at $MEMORY_BASE"

ISSUES=0
REQUIRED_DIRS=(
    "semantic/knowledge"
    "episodic/events"
    "procedural/scripts"
    "working/session"
    "index/search"
)

for d in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$MEMORY_BASE/$d" ]; then
        echo "[health] MISSING directory: $d"
        ISSUES=$((ISSUES+1))
        if $FIX; then
            mkdir -p "$MEMORY_BASE/$d"
            echo "[health] FIXED: created $d"
        fi
    fi
done

REQUIRED_FILES=(
    "semantic/facts.md"
    "semantic/concepts.md"
    "procedural/skills.md"
    "procedural/workflows.md"
    "working/current.md"
    "index/tags.json"
    "index/timeline.json"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$MEMORY_BASE/$f" ]; then
        echo "[health] MISSING file: $f"
        ISSUES=$((ISSUES+1))
        if $FIX; then
            case "$f" in
                *.json) echo '{}' > "$MEMORY_BASE/$f" ;;
                *)      echo "# $(basename $f .md)" > "$MEMORY_BASE/$f" ;;
            esac
            echo "[health] FIXED: created $f"
        fi
    fi
done

# Validate JSON files
for jf in "$MEMORY_BASE/index/tags.json" "$MEMORY_BASE/index/timeline.json"; do
    if [ -f "$jf" ]; then
        if ! jq empty "$jf" 2>/dev/null; then
            echo "[health] CORRUPT JSON: $jf"
            ISSUES=$((ISSUES+1))
            if $FIX; then
                echo '{}' > "$jf"
                echo "[health] FIXED: reset $jf"
            fi
        fi
    fi
done

if [ "$ISSUES" -eq 0 ]; then
    echo "[health] All checks passed. No issues found."
else
    echo "[health] Found $ISSUES issue(s)."
    if $FIX; then
        echo "[health] All fixable issues have been repaired."
        # Write repair log
        LOGDIR="${SCRIPT_DIR}/logs"
        mkdir -p "$LOGDIR"
        echo "health-check --fix ran at $(date -u +%Y-%m-%dT%H:%M:%SZ), fixed $ISSUES issues" >> "$LOGDIR/health.log"
    fi
fi
'''

# memory-backup.sh
backup_sh = r'''#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.json"
MEMORY_BASE=$(jq -r '.memory.base_path' "$CONFIG" 2>/dev/null || echo "./memory")
BACKUP_DEST=$(jq -r '.backup.output_path // "./backups"' "$CONFIG" 2>/dev/null || echo "./backups")

if [[ "$MEMORY_BASE" != /* ]]; then MEMORY_BASE="${SCRIPT_DIR}/${MEMORY_BASE}"; fi
if [[ "$BACKUP_DEST" != /* ]]; then BACKUP_DEST="${SCRIPT_DIR}/${BACKUP_DEST}"; fi

DRY_RUN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        --path)    MEMORY_BASE="$2"; shift 2 ;;
        --output)  BACKUP_DEST="$2"; shift 2 ;;
        *)         echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_NAME="memoria-backup-${TIMESTAMP}"
BACKUP_FILE="${BACKUP_DEST}/${BACKUP_NAME}.tar.gz"

if $VERBOSE; then
    echo "[backup] Memory source : $MEMORY_BASE"
    echo "[backup] Backup dest   : $BACKUP_DEST"
    echo "[backup] Backup file   : $BACKUP_FILE"
fi

if $DRY_RUN; then
    echo "[backup] DRY-RUN: would create $BACKUP_FILE"
    exit 0
fi

mkdir -p "$BACKUP_DEST"

if $VERBOSE; then
    echo "[backup] Creating archive..."
    tar -czvf "$BACKUP_FILE" -C "$(dirname "$MEMORY_BASE")" "$(basename "$MEMORY_BASE")"
else
    tar -czf  "$BACKUP_FILE" -C "$(dirname "$MEMORY_BASE")" "$(basename "$MEMORY_BASE")"
fi

echo "[backup] Backup created: $BACKUP_FILE"

# Write manifest
MANIFEST="${BACKUP_DEST}/manifest.json"
if [ -f "$MANIFEST" ]; then
    ENTRIES=$(jq -r '.backups' "$MANIFEST")
else
    ENTRIES="[]"
fi
echo "{\"backups\": $(echo $ENTRIES | jq ". + [{\"name\":\"${BACKUP_NAME}\",\"timestamp\":\"${TIMESTAMP}\",\"file\":\"${BACKUP_FILE}\"}]")}" > "$MANIFEST"
'''

# memory-rollback.sh
rollback_sh = r'''#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.json"
BACKUP_DEST=$(jq -r '.backup.output_path // "./backups"' "$CONFIG" 2>/dev/null || echo "./backups")
if [[ "$BACKUP_DEST" != /* ]]; then BACKUP_DEST="${SCRIPT_DIR}/${BACKUP_DEST}"; fi

cmd="${1:-}"
shift || true

case "$cmd" in
  list)
    echo "[rollback] Available backups in $BACKUP_DEST:"
    ls "$BACKUP_DEST"/*.tar.gz 2>/dev/null | while read f; do echo "  $(basename $f .tar.gz)"; done || echo "  (none)"
    ;;
  rollback)
    BACKUP_NAME="${1:-}"
    FORCE=false
    shift || true
    [[ "${1:-}" == "--force" ]] && FORCE=true
    BACKUP_FILE="${BACKUP_DEST}/${BACKUP_NAME}.tar.gz"
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "[rollback] ERROR: $BACKUP_FILE not found" >&2
        exit 1
    fi
    if ! $FORCE; then
        read -p "Restore from $BACKUP_NAME? [y/N] " answer
        [[ "$answer" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
    fi
    MEMORY_BASE=$(jq -r '.memory.base_path' "$CONFIG" 2>/dev/null || echo "./memory")
    if [[ "$MEMORY_BASE" != /* ]]; then MEMORY_BASE="${SCRIPT_DIR}/${MEMORY_BASE}"; fi
    echo "[rollback] Restoring $BACKUP_NAME -> $MEMORY_BASE"
    rm -rf "$MEMORY_BASE"
    tar -xzf "$BACKUP_FILE" -C "$(dirname "$MEMORY_BASE")"
    echo "[rollback] Restore complete."
    ;;
  *)
    echo "Usage: $0 {list|rollback BACKUP_NAME [--force]}" >&2
    exit 1
    ;;
esac
'''

# ─────────────────────────────────────────────
# 2.  Broken config.json (missing fields, wrong base_path)
# ─────────────────────────────────────────────
broken_config = {
    "memory": {
        "base_path": "./memory"
        # "structure" key intentionally absent
    },
    "backup": {
        "enabled": True,
        # retention_days intentionally missing
        "schedule": "0 2 * * *"
        # output_path intentionally missing
    }
    # health_check section intentionally absent
}

# ─────────────────────────────────────────────
# 3.  Corrupted memory structure
#     - episodic/ dir exists but events/ subdir is missing
#     - index/tags.json is corrupted (invalid JSON)
#     - index/timeline.json missing
#     - procedural/scripts/ missing
#     - working/session/ missing
#     - semantic/knowledge/ missing
# ─────────────────────────────────────────────

makedirs(MEMORIA_DIR)

# Write shell scripts
write_file(os.path.join(MEMORIA_DIR, "memory-migrate.sh"),       migrate_sh,  executable=True)
write_file(os.path.join(MEMORIA_DIR, "memory-health-check.sh"),  health_sh,   executable=True)
write_file(os.path.join(MEMORIA_DIR, "memory-backup.sh"),        backup_sh,   executable=True)
write_file(os.path.join(MEMORIA_DIR, "memory-rollback.sh"),      rollback_sh, executable=True)

# Write broken config
write_file(os.path.join(MEMORIA_DIR, "config.json"),
           json.dumps(broken_config, indent=2))

# Partial / corrupted memory tree
partial_memory = os.path.join(MEMORIA_DIR, "memory")

# semantic/ — partial (knowledge/ missing)
makedirs(partial_memory, "semantic")
write_file(os.path.join(partial_memory, "semantic", "facts.md"), "# Facts\n")
write_file(os.path.join(partial_memory, "semantic", "concepts.md"), "# Concepts\n")
# knowledge/ subdir intentionally ABSENT

# episodic/ — exists but events/ subdir missing
makedirs(partial_memory, "episodic")
write_file(os.path.join(partial_memory, "episodic", "2024-01-05.md"),
           "# Memory Log: 2024-01-05\n\nOld entry.\n")
# events/ intentionally ABSENT

# procedural/ — workflows.md present, skills.md present, scripts/ ABSENT
makedirs(partial_memory, "procedural")
write_file(os.path.join(partial_memory, "procedural", "skills.md"), "# Skills\n")
write_file(os.path.join(partial_memory, "procedural", "workflows.md"), "# Workflows\n")
# scripts/ intentionally ABSENT

# working/ — current.md present, session/ ABSENT
makedirs(partial_memory, "working")
write_file(os.path.join(partial_memory, "working", "current.md"),
           "# Current\n\nActive task: rebuild memory system.\n")
# session/ intentionally ABSENT

# index/ — tags.json CORRUPTED, timeline.json MISSING, search/ ABSENT
makedirs(partial_memory, "index")
write_file(os.path.join(partial_memory, "index", "tags.json"),
           "{ INVALID JSON !! tags: [null, ,, }")
# timeline.json intentionally ABSENT
# search/ intentionally ABSENT

# ─────────────────────────────────────────────
# 4.  Distractor files (10+)
# ─────────────────────────────────────────────
distractor_base = os.path.join(WORKSPACE, "projects")

# project-alpha: an unrelated Python project
makedirs(distractor_base, "project-alpha", "src")
write_file(os.path.join(distractor_base, "project-alpha", "src", "main.py"),
           "def main():\n    print('Hello, world')\n")
write_file(os.path.join(distractor_base, "project-alpha", "requirements.txt"),
           "flask==2.3.0\nrequests==2.31.0\n")
write_file(os.path.join(distractor_base, "project-alpha", "README.md"),
           "# Project Alpha\nNot related to memoria.\n")
write_file(os.path.join(distractor_base, "project-alpha", ".gitignore"),
           "__pycache__/\n*.pyc\n")

# project-beta: a Node.js project
makedirs(distractor_base, "project-beta", "lib")
write_file(os.path.join(distractor_base, "project-beta", "lib", "index.js"),
           "module.exports = {};\n")
write_file(os.path.join(distractor_base, "project-beta", "package.json"),
           json.dumps({"name": "project-beta", "version": "1.0.0"}, indent=2))
write_file(os.path.join(distractor_base, "project-beta", "Makefile"),
           "build:\n\tnode lib/index.js\n")

# old-backup: looks like a backup but is fake
makedirs(WORKSPACE, "old-backup")
write_file(os.path.join(WORKSPACE, "old-backup", "snapshot.tar.gz.txt"),
           "This is NOT a real backup file.\n")
write_file(os.path.join(WORKSPACE, "old-backup", "notes.txt"),
           "Legacy snapshot from 2023-06. Do not use.\n")

# docs: misleading documentation
makedirs(WORKSPACE, "docs")
write_file(os.path.join(WORKSPACE, "docs", "architecture.md"),
           "# System Architecture\nSee confluence for details.\n")
write_file(os.path.join(WORKSPACE, "docs", "migration-notes.txt"),
           "Migration to v2 pending.\nContacts: ops-team@example.com\n")

# stray config files
write_file(os.path.join(WORKSPACE, "settings.yaml"),
           "debug: true\nlog_level: info\n")
write_file(os.path.join(WORKSPACE, "deploy.sh"),
           "#!/usr/bin/env bash\necho 'deploy script placeholder'\n",
           executable=True)

# logs dir with old entries
makedirs(WORKSPACE, "logs")
write_file(os.path.join(WORKSPACE, "logs", "app-2024-01-01.log"),
           "[INFO] System started\n[ERROR] Memory path not found\n")
write_file(os.path.join(WORKSPACE, "logs", "app-2024-01-02.log"),
           "[INFO] Backup skipped\n")

print("Workspace generated successfully.")
print(f"Memoria system directory: {MEMORIA_DIR}")
print("Corrupted/partial memory structure created.")
print("Distractor files created.")