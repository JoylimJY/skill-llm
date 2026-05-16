#!/bin/bash
set -e

BASEDIR="/workspace/project/.openclaw"
SCRIPTS_DIR="$BASEDIR/scripts"
LOGS_DIR="$BASEDIR/logs"
SESSIONS_DIR="$BASEDIR/sessions"

mkdir -p "$SCRIPTS_DIR" "$LOGS_DIR" "$SESSIONS_DIR"

# -----------------------------------------------------------------------
# MOCK: start-tmux-task.sh
# Accepts: --label, --workdir, --prompt-file, --task
# Records invocation, creates a session file, outputs session info
# -----------------------------------------------------------------------
cat > "$SCRIPTS_DIR/start-tmux-task.sh" << 'MOCK_EOF'
#!/bin/bash
LABEL=""
WORKDIR=""
PROMPT_FILE=""
TASK=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --label) LABEL="$2"; shift 2 ;;
        --workdir) WORKDIR="$2"; shift 2 ;;
        --prompt-file) PROMPT_FILE="$2"; shift 2 ;;
        --task) TASK="$2"; shift 2 ;;
        *) shift ;;
    esac
done

BASEDIR="/workspace/project/.openclaw"
LOGS_DIR="$BASEDIR/logs"
SESSIONS_DIR="$BASEDIR/sessions"

# Log the invocation
echo "label=$LABEL workdir=$WORKDIR prompt_file=$PROMPT_FILE task=$TASK" >> "$LOGS_DIR/start-invocations.log"

if [[ -z "$LABEL" || -z "$WORKDIR" || -z "$PROMPT_FILE" ]]; then
    echo "ERROR: --label, --workdir, and --prompt-file are required" >&2
    exit 1
fi

# Validate prompt file contains wake callback
if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "ERROR: prompt file not found: $PROMPT_FILE" >&2
    exit 1
fi

if ! grep -q "wake.sh" "$PROMPT_FILE"; then
    echo "WARNING: prompt file does not contain wake.sh callback" >&2
fi

SESSION_NAME="cc-${LABEL}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create session state file
cat > "$SESSIONS_DIR/${LABEL}.json" << SESS_EOF
{
  "label": "${LABEL}",
  "session": "${SESSION_NAME}",
  "status": "running",
  "sessionAlive": true,
  "workdir": "${WORKDIR}",
  "promptFile": "${PROMPT_FILE}",
  "startedAt": "${TIMESTAMP}"
}
SESS_EOF

echo "Session started: $SESSION_NAME"
echo "Attach command: bash $BASEDIR/scripts/monitor-tmux-task.sh --attach --session $SESSION_NAME"
echo "Status command: bash $BASEDIR/scripts/status-tmux-task.sh --label $LABEL"
MOCK_EOF

# -----------------------------------------------------------------------
# MOCK: status-tmux-task.sh
# Accepts: --label
# Returns: STATUS=likely_done (simulating task has completed)
# -----------------------------------------------------------------------
cat > "$SCRIPTS_DIR/status-tmux-task.sh" << 'MOCK_EOF'
#!/bin/bash
LABEL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --label) LABEL="$2"; shift 2 ;;
        *) shift ;;
    esac
done

BASEDIR="/workspace/project/.openclaw"
LOGS_DIR="$BASEDIR/logs"
SESSIONS_DIR="$BASEDIR/sessions"

echo "label=$LABEL" >> "$LOGS_DIR/status-invocations.log"

if [[ -z "$LABEL" ]]; then
    echo "ERROR: --label is required" >&2
    exit 1
fi

if [[ ! -f "$SESSIONS_DIR/${LABEL}.json" ]]; then
    echo "STATUS=dead"
    exit 0
fi

# Simulate: task is now complete (likely_done)
echo "STATUS=likely_done"
MOCK_EOF

# -----------------------------------------------------------------------
# MOCK: complete-tmux-task.sh
# Accepts: --label, --workdir
# Generates the completion report JSON + MD at /tmp/cc-<label>-completion-report.*
# -----------------------------------------------------------------------
cat > "$SCRIPTS_DIR/complete-tmux-task.sh" << 'MOCK_EOF'
#!/bin/bash
LABEL=""
WORKDIR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --label) LABEL="$2"; shift 2 ;;
        --workdir) WORKDIR="$2"; shift 2 ;;
        *) shift ;;
    esac
done

BASEDIR="/workspace/project/.openclaw"
LOGS_DIR="$BASEDIR/logs"

echo "label=$LABEL workdir=$WORKDIR" >> "$LOGS_DIR/complete-invocations.log"

if [[ -z "$LABEL" || -z "$WORKDIR" ]]; then
    echo "ERROR: --label and --workdir are required" >&2
    exit 1
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
REPORT_JSON="/tmp/cc-${LABEL}-completion-report.json"
REPORT_MD="/tmp/cc-${LABEL}-completion-report.md"

# Write JSON report
cat > "$REPORT_JSON" << REPORT_EOF
{
  "label": "${LABEL}",
  "status": "completed",
  "workdir": "${WORKDIR}",
  "completedAt": "${TIMESTAMP}",
  "filesModified": [
    "src/risk_engine/var_calculator.py",
    "src/risk_engine/monte_carlo_var.py",
    "src/portfolio/position_manager.py",
    "tests/unit/test_var.py",
    "tests/unit/test_monte_carlo.py"
  ],
  "testsRun": 12,
  "testsPassed": 12,
  "testsFailed": 0,
  "lintErrors": 0,
  "riskLevel": "low",
  "summary": "Refactored VaR calculator to support Monte Carlo simulation with 10000 iterations. Fixed thread-safety in PositionManager using RLock. All 12 unit tests passing. No breaking API changes.",
  "nextSteps": [
    "Review Monte Carlo convergence on historical data",
    "Run integration tests with mocked market data feed",
    "Update architecture.md documentation"
  ]
}
REPORT_EOF

# Write MD report
cat > "$REPORT_MD" << REPORT_EOF
# Completion Report: ${LABEL}

**Status:** Completed  
**Completed At:** ${TIMESTAMP}

## Summary
Refactored VaR calculator to support Monte Carlo simulation with 10000 iterations. Fixed thread-safety in PositionManager using RLock. All 12 unit tests passing. No breaking API changes.

## Files Modified
- src/risk_engine/var_calculator.py
- src/risk_engine/monte_carlo_var.py
- src/portfolio/position_manager.py
- tests/unit/test_var.py
- tests/unit/test_monte_carlo.py

## Test Results
- Tests Run: 12
- Tests Passed: 12
- Tests Failed: 0
- Lint Errors: 0

## Risk Assessment
**Risk Level:** low

## Next Steps
1. Review Monte Carlo convergence on historical data
2. Run integration tests with mocked market data feed
3. Update architecture.md documentation
REPORT_EOF

echo "Completion report written:"
echo "  JSON: $REPORT_JSON"
echo "  MD:   $REPORT_MD"
MOCK_EOF

# -----------------------------------------------------------------------
# MOCK: monitor-tmux-task.sh
# Accepts: --session, --lines, --attach
# -----------------------------------------------------------------------
cat > "$SCRIPTS_DIR/monitor-tmux-task.sh" << 'MOCK_EOF'
#!/bin/bash
SESSION=""
LINES=200
ATTACH=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --session) SESSION="$2"; shift 2 ;;
        --lines) LINES="$2"; shift 2 ;;
        --attach) ATTACH=true; shift ;;
        *) shift ;;
    esac
done

BASEDIR="/workspace/project/.openclaw"
LOGS_DIR="$BASEDIR/logs"

echo "session=$SESSION lines=$LINES attach=$ATTACH" >> "$LOGS_DIR/monitor-invocations.log"

if [[ "$ATTACH" == "true" ]]; then
    echo "Attaching to session $SESSION (mock: would open tmux)"
    exit 0
fi

echo "[tmux capture - last $LINES lines of $SESSION]"
echo "Claude Code: Analyzing codebase..."
echo "Claude Code: Implementing Monte Carlo VaR..."
echo "Claude Code: Fixing thread-safety in PositionManager..."
echo "Claude Code: Running tests... 12/12 passed."
echo "Claude Code: Writing completion report."
echo "Claude Code: Task complete. Calling wake callback."
MOCK_EOF

# -----------------------------------------------------------------------
# MOCK: list-tasks.sh
# Accepts: --json, --lines, --socket
# -----------------------------------------------------------------------
cat > "$SCRIPTS_DIR/list-tasks.sh" << 'MOCK_EOF'
#!/bin/bash
JSON_MODE=false
LINES=20

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json) JSON_MODE=true; shift ;;
        --lines) LINES="$2"; shift 2 ;;
        --socket) shift 2 ;;
        *) shift ;;
    esac
done

BASEDIR="/workspace/project/.openclaw"
SESSIONS_DIR="$BASEDIR/sessions"
LOGS_DIR="$BASEDIR/logs"

echo "json=$JSON_MODE lines=$LINES" >> "$LOGS_DIR/list-invocations.log"

if [[ "$JSON_MODE" == "true" ]]; then
    TASKS_JSON="[]"
    if ls "$SESSIONS_DIR"/*.json 1>/dev/null 2>&1; then
        TASKS_JSON="["
        FIRST=true
        for f in "$SESSIONS_DIR"/*.json; do
            LABEL=$(python3 -c "import json,sys; d=json.load(open('$f')); print(d['label'])")
            SESSION=$(python3 -c "import json,sys; d=json.load(open('$f')); print(d['session'])")
            REPORT_JSON="/tmp/cc-${LABEL}-completion-report.json"
            REPORT_EXISTS="false"
            [[ -f "$REPORT_JSON" ]] && REPORT_EXISTS="true"
            if [[ "$FIRST" == "false" ]]; then TASKS_JSON+=","; fi
            TASKS_JSON+="{\"label\":\"$LABEL\",\"session\":\"$SESSION\",\"status\":\"likely_done\",\"sessionAlive\":false,\"reportExists\":$REPORT_EXISTS,\"reportJsonPath\":\"$REPORT_JSON\",\"lastLines\":[\"Task complete.\"],\"updatedAt\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}"
            FIRST=false
        done
        TASKS_JSON+="]"
    fi
    echo "$TASKS_JSON"
else
    if ls "$SESSIONS_DIR"/*.json 1>/dev/null 2>&1; then
        for f in "$SESSIONS_DIR"/*.json; do
            LABEL=$(python3 -c "import json,sys; d=json.load(open('$f')); print(d['label'])")
            echo "[$LABEL] status=likely_done | Task complete."
        done
    else
        echo "No active cc-* tasks."
    fi
fi
MOCK_EOF

# -----------------------------------------------------------------------
# MOCK: wake.sh
# -----------------------------------------------------------------------
cat > "$SCRIPTS_DIR/wake.sh" << 'MOCK_EOF'
#!/bin/bash
MESSAGE="${1:-}"
WHEN="${2:-}"
BASEDIR="/workspace/project/.openclaw"
LOGS_DIR="$BASEDIR/logs"
echo "message=$MESSAGE when=$WHEN" >> "$LOGS_DIR/wake-invocations.log"
echo "Wake signal sent: $MESSAGE (timing: $WHEN)"
MOCK_EOF

# Make all scripts executable
chmod +x "$SCRIPTS_DIR/"*.sh

echo "Mock scripts installed at $SCRIPTS_DIR"
echo "All scripts are executable."
ls -la "$SCRIPTS_DIR/"