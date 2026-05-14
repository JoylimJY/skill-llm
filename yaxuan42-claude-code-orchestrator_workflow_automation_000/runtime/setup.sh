#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Set up the Claude Code Orchestrator skill environment
# This simulates the {baseDir} infrastructure
# ============================================================

BASEDIR="/opt/openclaw"
mkdir -p "$BASEDIR/scripts"
mkdir -p "$TMPDIR/clawdbot-tmux-sockets" 2>/dev/null || mkdir -p "/tmp/clawdbot-tmux-sockets"

# Invocation log — all mock scripts append here so eval can inspect calls
INVOCATION_LOG="/tmp/skill_invocations.log"
touch "$INVOCATION_LOG"

# ---- Script: start-tmux-task.sh ----
cat > "$BASEDIR/scripts/start-tmux-task.sh" << 'SCRIPT_EOF'
#!/usr/bin/env bash
# Mock: start-tmux-task.sh
LABEL=""
WORKDIR=""
PROMPT_FILE=""
TASK=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) LABEL="$2"; shift 2;;
    --workdir) WORKDIR="$2"; shift 2;;
    --prompt-file) PROMPT_FILE="$2"; shift 2;;
    --task) TASK="$2"; shift 2;;
    *) shift;;
  esac
done

INVOCATION_LOG="/tmp/skill_invocations.log"
echo "start-tmux-task.sh --label=${LABEL} --workdir=${WORKDIR} --prompt-file=${PROMPT_FILE} --task=${TASK}" >> "$INVOCATION_LOG"

if [[ -z "$LABEL" || -z "$WORKDIR" || -z "$PROMPT_FILE" ]]; then
  echo "ERROR: missing required args (--label, --workdir, --prompt-file)" >&2
  exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "ERROR: prompt file not found: $PROMPT_FILE" >&2
  exit 1
fi

# Verify the prompt file contains the mandatory wake.sh callback
if ! grep -q "wake.sh" "$PROMPT_FILE"; then
  echo "WARNING: prompt file does not contain wake.sh callback" >> "$INVOCATION_LOG"
fi

SESSION="cc-${LABEL}"
echo "Session started: ${SESSION}" 
echo "Attach: tmux -S /tmp/clawdbot-tmux-sockets/clawdbot.sock attach -t ${SESSION}"
echo "STATUS=running"
echo "${SESSION}" > "/tmp/cc-${LABEL}-session.txt"
SCRIPT_EOF

# ---- Script: status-tmux-task.sh ----
cat > "$BASEDIR/scripts/status-tmux-task.sh" << 'SCRIPT_EOF'
#!/usr/bin/env bash
# Mock: status-tmux-task.sh — always returns likely_done after start
LABEL=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) LABEL="$2"; shift 2;;
    *) shift;;
  esac
done

echo "status-tmux-task.sh --label=${LABEL}" >> /tmp/skill_invocations.log

if [[ -f "/tmp/cc-${LABEL}-session.txt" ]]; then
  echo "STATUS=likely_done"
else
  echo "STATUS=idle"
fi
SCRIPT_EOF

# ---- Script: monitor-tmux-task.sh ----
cat > "$BASEDIR/scripts/monitor-tmux-task.sh" << 'SCRIPT_EOF'
#!/usr/bin/env bash
# Mock: monitor-tmux-task.sh
SESSION=""
LINES=200
ATTACH=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --session) SESSION="$2"; shift 2;;
    --lines) LINES="$2"; shift 2;;
    --attach) ATTACH=1; shift;;
    *) shift;;
  esac
done

echo "monitor-tmux-task.sh --session=${SESSION} --lines=${LINES}" >> /tmp/skill_invocations.log

echo "[Simulated tmux output - last ${LINES} lines]"
echo "Claude: Analyzing factor_model.py..."
echo "Claude: Implementing OLS regression for Fama-French factors..."
echo "Claude: Writing type annotations and docstrings..."
echo "Claude: Running smoke test..."
echo "Claude: All checks passed. Task complete."
SCRIPT_EOF

# ---- Script: list-tasks.sh ----
cat > "$BASEDIR/scripts/list-tasks.sh" << 'SCRIPT_EOF'
#!/usr/bin/env bash
# Mock: list-tasks.sh
JSON=0
LINES=20
while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON=1; shift;;
    --lines) LINES="$2"; shift 2;;
    --socket) shift 2;;
    *) shift;;
  esac
done

echo "list-tasks.sh --json=${JSON} --lines=${LINES}" >> /tmp/skill_invocations.log

# Discover any running sessions from session files
TASKS="[]"
for f in /tmp/cc-*-session.txt; do
  [[ -f "$f" ]] || continue
  BASENAME=$(basename "$f" -session.txt)
  LABEL="${BASENAME#cc-}"
  SESSION="cc-${LABEL}"
  REPORT_PATH="/tmp/cc-${LABEL}-completion-report.json"
  REPORT_EXISTS="false"
  [[ -f "$REPORT_PATH" ]] && REPORT_EXISTS="true"
  
  ENTRY=$(cat <<JSON
{
  "label": "${LABEL}",
  "session": "${SESSION}",
  "status": "likely_done",
  "sessionAlive": false,
  "reportExists": ${REPORT_EXISTS},
  "reportJsonPath": "${REPORT_PATH}",
  "lastLines": "Claude: Task complete.",
  "updatedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
JSON
)
  if [[ "$TASKS" == "[]" ]]; then
    TASKS="[${ENTRY}]"
  else
    TASKS="${TASKS%]},${ENTRY}]"
  fi
done

if [[ $JSON -eq 1 ]]; then
  echo "$TASKS"
else
  echo "=== Active cc-* Tasks ==="
  echo "$TASKS" | python3 -c "
import json,sys
tasks=json.load(sys.stdin)
for t in tasks:
    print(f\"  [{t['status']}] {t['label']} | session={t['session']} | reportExists={t['reportExists']}\")
"
fi
SCRIPT_EOF

# ---- Script: complete-tmux-task.sh ----
cat > "$BASEDIR/scripts/complete-tmux-task.sh" << 'SCRIPT_EOF'
#!/usr/bin/env bash
# Mock: complete-tmux-task.sh — generates completion report
LABEL=""
WORKDIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) LABEL="$2"; shift 2;;
    --workdir) WORKDIR="$2"; shift 2;;
    *) shift;;
  esac
done

echo "complete-tmux-task.sh --label=${LABEL} --workdir=${WORKDIR}" >> /tmp/skill_invocations.log

if [[ -z "$LABEL" ]]; then
  echo "ERROR: --label required" >&2
  exit 1
fi

REPORT_JSON="/tmp/cc-${LABEL}-completion-report.json"
REPORT_MD="/tmp/cc-${LABEL}-completion-report.md"

cat > "$REPORT_JSON" << REPORTEOF
{
  "label": "${LABEL}",
  "workdir": "${WORKDIR}",
  "status": "completed",
  "completedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "filesModified": [
    "${WORKDIR}/src/models/factor_model.py"
  ],
  "filesCreated": [],
  "lintStatus": "passed",
  "testStatus": "passed",
  "summary": "Implemented Fama-French 3-factor model using OLS regression. Added factor_exposure() and residual_risk() functions with NumPy-style docstrings and type annotations.",
  "risks": [
    "No integration tests for the new factor_model — only smoke test was run",
    "scipy.stats dependency was used for OLS (check if allowed)"
  ],
  "nextSteps": [
    "Add integration test fixtures in tests/integration/",
    "Review scipy dependency against project constraints",
    "Run full test suite before merging"
  ]
}
REPORTEOF

cat > "$REPORT_MD" << MDEOF
# Completion Report: ${LABEL}

## Status: COMPLETED

## Summary
Implemented Fama-French 3-factor model with OLS regression.

## Files Modified
- ${WORKDIR}/src/models/factor_model.py

## Risks
- No integration tests
- scipy dependency introduced

## Next Steps
1. Add integration test fixtures
2. Review scipy dependency
3. Full test suite
MDEOF

echo "Report generated: ${REPORT_JSON}"
echo "Report generated: ${REPORT_MD}"
SCRIPT_EOF

# ---- Script: wake.sh ----
cat > "$BASEDIR/scripts/wake.sh" << 'SCRIPT_EOF'
#!/usr/bin/env bash
# Mock: wake.sh — simulates OpenClaw wake callback
MESSAGE="${1:-no message}"
TIMING="${2:-now}"
echo "wake.sh called: message='${MESSAGE}' timing='${TIMING}'" >> /tmp/skill_invocations.log
echo "[WAKE] Callback registered: ${MESSAGE} (${TIMING})"
SCRIPT_EOF

chmod +x "$BASEDIR/scripts/start-tmux-task.sh"
chmod +x "$BASEDIR/scripts/status-tmux-task.sh"
chmod +x "$BASEDIR/scripts/monitor-tmux-task.sh"
chmod +x "$BASEDIR/scripts/list-tasks.sh"
chmod +x "$BASEDIR/scripts/complete-tmux-task.sh"
chmod +x "$BASEDIR/scripts/wake.sh"

# ---- Expose BASEDIR to agents via a well-known location ----
echo "$BASEDIR" > /etc/openclaw-basedir
echo "export OPENCLAW_BASEDIR=$BASEDIR" >> /etc/environment
echo "export OPENCLAW_BASEDIR=$BASEDIR" >> /root/.bashrc

# Make scripts globally accessible
ln -sf "$BASEDIR/scripts/start-tmux-task.sh"    /usr/local/bin/start-tmux-task
ln -sf "$BASEDIR/scripts/status-tmux-task.sh"   /usr/local/bin/status-tmux-task
ln -sf "$BASEDIR/scripts/monitor-tmux-task.sh"  /usr/local/bin/monitor-tmux-task
ln -sf "$BASEDIR/scripts/list-tasks.sh"         /usr/local/bin/list-tasks
ln -sf "$BASEDIR/scripts/complete-tmux-task.sh" /usr/local/bin/complete-tmux-task
ln -sf "$BASEDIR/scripts/wake.sh"               /usr/local/bin/wake

echo "OpenClaw orchestration environment ready."
echo "BASEDIR: $BASEDIR"
echo "Scripts available at: $BASEDIR/scripts/"