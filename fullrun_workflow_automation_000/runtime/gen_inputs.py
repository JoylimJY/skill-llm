import os
import random
import stat

random.seed(42)

workspace = "/workspace"

# --- Create realistic distractor directory structure ---
dirs = [
    "data/raw/samples",
    "data/processed/output",
    "data/interim/staging",
    "src/pipeline/steps",
    "src/utils",
    "src/validators",
    "tests/unit",
    "tests/integration",
    "docs/api",
    "configs/environments",
    "notebooks",
    "logs",
    "scripts",  # This is the REAL scripts dir per SKILL.md
    ".claude",  # Distractor — empty, install should populate it
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "data/raw/samples/genome_batch_001.fastq": ">SEQ001\nATCGATCGATCG\n>SEQ002\nGGCCTTAAGGCC\n",
    "data/raw/samples/genome_batch_002.fastq": ">SEQ003\nTTTAAAGGGCCC\n>SEQ004\nACACACGTGTGT\n",
    "data/processed/output/alignment_summary.txt": "Total reads: 4821\nMapped: 4612 (95.6%)\nUnmapped: 209 (4.4%)\n",
    "data/interim/staging/.gitkeep": "",
    "src/pipeline/steps/quality_filter.py": "# Quality filter stub\ndef filter_reads(path): pass\n",
    "src/pipeline/steps/alignment.py": "# Alignment stub\ndef align(ref, reads): pass\n",
    "src/utils/file_helpers.py": "import os\ndef list_files(d): return os.listdir(d)\n",
    "src/validators/schema_check.py": "def validate(schema, data): return True\n",
    "tests/unit/test_helpers.py": "import unittest\nclass TestHelpers(unittest.TestCase): pass\n",
    "tests/integration/test_pipeline.py": "# Integration test placeholder\n",
    "docs/api/endpoints.md": "# API Reference\n\n## POST /process\nSubmits a batch job.\n",
    "configs/environments/dev.yaml": "env: dev\ndb_host: localhost\ndb_port: 5432\n",
    "configs/environments/prod.yaml": "env: prod\ndb_host: db.biolab.internal\ndb_port: 5432\n",
    "notebooks/exploratory_analysis.py": "# EDA notebook\nimport csv\n# TODO: load genome data\n",
    "logs/pipeline_run_20240101.log": "[INFO] Pipeline started\n[INFO] Step 1 complete\n[WARN] Low coverage at chr7\n[INFO] Pipeline finished\n",
    "src/utils/logger.py": "import logging\nlogging.basicConfig(level=logging.INFO)\n",
    "src/pipeline/steps/variant_calling.py": "# Variant calling stub\ndef call_variants(bam): pass\n",
    "tests/unit/test_validators.py": "# Validator tests\n",
    ".claude/README_PLACEHOLDER": "# This directory is managed by project tooling\n",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the REAL scripts as per SKILL.md ---
# These scripts are what the agent must invoke; they already exist per the skill spec.

install_sh = r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLAUDE_DIR="$PROJECT_DIR/.claude"
FULLRUN_SCRIPTS_DIR="$CLAUDE_DIR/fullrun/scripts"
SETTINGS_FILE="$CLAUDE_DIR/settings.local.json"

echo "[install] Creating .claude/fullrun/scripts/ directory..."
mkdir -p "$FULLRUN_SCRIPTS_DIR"

echo "[install] Copying scripts..."
for script in main.sh fullrun.sh cron-manager.sh; do
    cp "$SCRIPT_DIR/$script" "$FULLRUN_SCRIPTS_DIR/$script"
    chmod +x "$FULLRUN_SCRIPTS_DIR/$script"
done

echo "[install] Setting up .claude/settings.local.json..."
if [ ! -f "$SETTINGS_FILE" ]; then
    cat > "$SETTINGS_FILE" <<'EOF'
{
  "permissions": {
    "allow": [
      "Bash(.claude/fullrun/scripts/*)"
    ]
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/fullrun/scripts/main.sh start"
          }
        ]
      }
    ]
  }
}
EOF
else
    echo "[install] settings.local.json already exists, updating..."
    # Add permission if not present
    if ! jq -e '.permissions.allow[] | select(. == "Bash(.claude/fullrun/scripts/*)")' "$SETTINGS_FILE" > /dev/null 2>&1; then
        jq '.permissions.allow += ["Bash(.claude/fullrun/scripts/*)"]' "$SETTINGS_FILE" > "${SETTINGS_FILE}.tmp" && mv "${SETTINGS_FILE}.tmp" "$SETTINGS_FILE"
    fi
fi

echo "[install] Installation complete."
echo "[install] Scripts installed to: $FULLRUN_SCRIPTS_DIR"
echo "[install] Run: ./.claude/fullrun/scripts/main.sh start"
"""

fullrun_sh = r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
STATUS_FILE="$PROJECT_DIR/.claude-status.txt"
CHECKLIST_FILE="$PROJECT_DIR/checklist.md"
LOG_FILE="$PROJECT_DIR/.fullrun.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

get_status() {
    if [ ! -f "$STATUS_FILE" ]; then
        echo "0"
    else
        cat "$STATUS_FILE"
    fi
}

set_status() {
    echo "$1" > "$STATUS_FILE"
    log "Status set to: $1"
}

get_pending_tasks() {
    if [ ! -f "$CHECKLIST_FILE" ]; then
        echo ""
        return
    fi
    grep -n '^\- \[ \]' "$CHECKLIST_FILE" | head -1 || true
}

count_pending() {
    if [ ! -f "$CHECKLIST_FILE" ]; then
        echo "0"
        return
    fi
    grep -c '^\- \[ \]' "$CHECKLIST_FILE" || echo "0"
}

mark_task_complete() {
    local line_num="$1"
    awk -v ln="$line_num" 'NR==ln { sub(/\[ \]/, "[x]") } { print }' "$CHECKLIST_FILE" > "${CHECKLIST_FILE}.tmp" && mv "${CHECKLIST_FILE}.tmp" "$CHECKLIST_FILE"
    log "Marked task on line $line_num as complete"
}

run_tasks() {
    local current_status
    current_status=$(get_status)

    if [ "$current_status" = "1" ]; then
        log "Execution already in progress (status=1). Skipping."
        return
    fi

    local pending_count
    pending_count=$(count_pending)

    if [ "$pending_count" -eq 0 ]; then
        log "No pending tasks found."
        set_status "2"
        return
    fi

    set_status "1"
    log "Starting task execution. Pending tasks: $pending_count"

    while true; do
        local task_line
        task_line=$(get_pending_tasks)
        if [ -z "$task_line" ]; then
            log "All tasks completed."
            break
        fi

        local line_num
        line_num=$(echo "$task_line" | cut -d: -f1)
        local task_desc
        task_desc=$(echo "$task_line" | sed 's/^[0-9]*:- \[ \] //')

        log "Executing task (line $line_num): $task_desc"
        # Simulate task execution
        sleep 0.1
        mark_task_complete "$line_num"
        log "Task completed: $task_desc"
    done

    set_status "2"
    log "All tasks finished. Status set to 2."
}

case "${1:-}" in
    run) run_tasks ;;
    count) count_pending ;;
    status) get_status ;;
    *)
        echo "Usage: $0 {run|count|status}"
        exit 1
        ;;
esac
"""

cron_manager_sh = r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
STATUS_FILE="$PROJECT_DIR/.claude-status.txt"
CHECKLIST_FILE="$PROJECT_DIR/checklist.md"
LOG_FILE="$PROJECT_DIR/.fullrun.log"
PID_FILE="$PROJECT_DIR/.monitor.pid"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [monitor] $*" | tee -a "$LOG_FILE"
}

get_status() {
    if [ ! -f "$STATUS_FILE" ]; then echo "0"; else cat "$STATUS_FILE"; fi
}

monitor_loop() {
    log "Monitor started (PID: $$)"
    echo $$ > "$PID_FILE"

    while true; do
        local status
        status=$(get_status)

        case "$status" in
            "2")
                log "All tasks completed (status=2). Exiting monitor."
                rm -f "$PID_FILE"
                exit 0
                ;;
            "1")
                log "Execution in progress (status=1). Waiting..."
                ;;
            *)
                if [ -f "$CHECKLIST_FILE" ]; then
                    local pending
                    pending=$(grep -c '^\- \[ \]' "$CHECKLIST_FILE" 2>/dev/null || echo "0")
                    if [ "$pending" -gt 0 ]; then
                        log "Pending tasks found (status=0). Triggering execution."
                        "$SCRIPT_DIR/fullrun.sh" run
                    else
                        log "No pending tasks. Setting status to 2."
                        echo "2" > "$STATUS_FILE"
                        rm -f "$PID_FILE"
                        exit 0
                    fi
                fi
                ;;
        esac
        sleep 60
    done
}

stop_monitor() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log "Monitor stopped (PID: $pid)"
        fi
        rm -f "$PID_FILE"
    else
        echo "No monitor running."
    fi
}

case "${1:-}" in
    start) monitor_loop ;;
    stop) stop_monitor ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac
"""

main_sh = r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
STATUS_FILE="$PROJECT_DIR/.claude-status.txt"
LOG_FILE="$PROJECT_DIR/.fullrun.log"
PID_FILE="$PROJECT_DIR/.monitor.pid"

get_status() {
    if [ ! -f "$STATUS_FILE" ]; then echo "0"; else cat "$STATUS_FILE"; fi
}

case "${1:-help}" in
    start)
        echo "[main] Starting scheduled monitoring..."
        nohup "$SCRIPT_DIR/cron-manager.sh" start >> "$LOG_FILE" 2>&1 &
        echo "[main] Monitor started in background."
        ;;
    run)
        echo "[main] Running tasks manually..."
        "$SCRIPT_DIR/fullrun.sh" run
        ;;
    status)
        status=$(get_status)
        echo "[main] Current status: $status"
        case "$status" in
            "0") echo "[main] State: Idle / Ready" ;;
            "1") echo "[main] State: Executing tasks" ;;
            "2") echo "[main] State: All tasks completed" ;;
        esac
        ;;
    stop)
        "$SCRIPT_DIR/cron-manager.sh" stop
        ;;
    help|*)
        echo "Usage: $0 {start|run|status|stop}"
        echo "  start  - Start scheduled monitoring (background)"
        echo "  run    - Manually execute pending tasks"
        echo "  status - Check current execution status"
        echo "  stop   - Stop background monitor"
        ;;
esac
"""

uninstall_sh = r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLAUDE_DIR="$PROJECT_DIR/.claude"
FULLRUN_DIR="$CLAUDE_DIR/fullrun"
SETTINGS_FILE="$CLAUDE_DIR/settings.local.json"

echo "[uninstall] Removing .claude/fullrun/ directory..."
rm -rf "$FULLRUN_DIR"

if [ -f "$SETTINGS_FILE" ]; then
    echo "[uninstall] Removing fullrun entries from settings.local.json..."
    # Remove fullrun permission rule
    jq 'del(.permissions.allow[] | select(. == "Bash(.claude/fullrun/scripts/*)"))' "$SETTINGS_FILE" > "${SETTINGS_FILE}.tmp" && mv "${SETTINGS_FILE}.tmp" "$SETTINGS_FILE"
    # Remove fullrun hook
    jq 'del(.hooks.SessionStart[].hooks[] | select(.command == ".claude/fullrun/scripts/main.sh start"))' "$SETTINGS_FILE" > "${SETTINGS_FILE}.tmp" && mv "${SETTINGS_FILE}.tmp" "$SETTINGS_FILE"
    # Check if settings is now empty/trivial
    local_settings=$(jq '{permissions: {allow: (.permissions.allow // [])}, hooks: (.hooks // {})}' "$SETTINGS_FILE")
    allow_count=$(echo "$local_settings" | jq '.permissions.allow | length')
    hooks_count=$(echo "$local_settings" | jq '.hooks | length')
    if [ "$allow_count" -eq 0 ] && [ "$hooks_count" -eq 0 ]; then
        echo "[uninstall] settings.local.json is now empty. Removing."
        rm -f "$SETTINGS_FILE"
    fi
fi
echo "[uninstall] Uninstall complete."
"""

scripts = {
    "scripts/install.sh": install_sh,
    "scripts/uninstall.sh": uninstall_sh,
    "scripts/main.sh": main_sh,
    "scripts/fullrun.sh": fullrun_sh,
    "scripts/cron-manager.sh": cron_manager_sh,
}

for path, content in scripts.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)
    os.chmod(full_path, os.stat(full_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# --- DO NOT create checklist.md or .claude-status.txt — the agent must do this ---
# --- DO NOT create .claude/fullrun/ — install.sh must do this ---

# Remove the placeholder we added to .claude/ to keep it as a real distractor
os.remove(os.path.join(workspace, ".claude/README_PLACEHOLDER"))

print("Workspace generated successfully.")
print("Scripts created in scripts/ directory.")
print("checklist.md NOT created — agent must create it.")
print(".claude-status.txt NOT created — will be managed by scripts.")