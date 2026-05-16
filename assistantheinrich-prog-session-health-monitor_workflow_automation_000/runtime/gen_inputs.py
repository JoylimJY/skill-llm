#!/usr/bin/env python3
"""
Build the sandbox workspace for the session-health-monitor skill task.
This creates all necessary files deterministically.
"""

import os
import stat
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ─────────────────────────────────────────────
# 1. Directory structure
# ─────────────────────────────────────────────
dirs = [
    "scripts",
    "memory",
    "memory/archive",
    "shared",
    "logs",
    "agents/compliance-auditor",
    "agents/compliance-auditor/config",
    "agents/compliance-auditor/outputs",
    "agents/risk-scanner",
    "agents/risk-scanner/config",
    "data/raw",
    "data/processed",
    "reports/weekly",
    "reports/monthly",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 2. Distractor files
# ─────────────────────────────────────────────
distractors = {
    "shared/INDEX.md": "| General utilities | `skill-utils.md` |\n| Network checks | `skill-net.md` |\n",
    "agents/compliance-auditor/config/agent.yaml": (
        "name: compliance-auditor\nversion: 2.1\nheartbeat: 30s\nmax_context: 200000\n"
    ),
    "agents/compliance-auditor/outputs/last_run.txt": (
        "Run completed at 2024-03-15T09:12:00Z\nDuration: 4h 23m\nItems audited: 1482\n"
    ),
    "agents/risk-scanner/config/thresholds.json": (
        '{"risk_high": 0.85, "risk_medium": 0.55, "alert_email": "ops@fintech.internal"}\n'
    ),
    "logs/agent-2024-03-14.log": (
        "[INFO] Agent started\n[INFO] Loaded 3 skills\n[WARN] Context at 48%\n[INFO] Task complete\n"
    ),
    "logs/agent-2024-03-15.log": (
        "[INFO] Agent started\n[INFO] Context compacted (drop detected)\n[WARN] Context at 71%\n"
    ),
    "data/raw/transactions_2024Q1.csv": (
        "id,amount,currency,status\n1001,5000.00,USD,cleared\n1002,250.50,EUR,pending\n"
    ),
    "data/processed/transactions_summary.json": (
        '{"total": 2, "cleared": 1, "pending": 1, "flagged": 0}\n'
    ),
    "reports/weekly/week12_2024.md": (
        "# Week 12 Summary\n- 3 agents active\n- 0 critical alerts\n- Context rotations: 2\n"
    ),
    "reports/monthly/march_2024.md": (
        "# March 2024\n- Compliance checks: 847\n- Issues found: 12\n- Resolved: 10\n"
    ),
    "agents/risk-scanner/config/rules.yaml": (
        "rules:\n  - id: R001\n    pattern: high_value_transfer\n    threshold: 10000\n"
    ),
    "agents/compliance-auditor/config/schedule.cron": (
        "0 */4 * * * /usr/local/bin/run-audit.sh\n"
    ),
}
for path, content in distractors.items():
    (WORKSPACE / path).write_text(content)

# ─────────────────────────────────────────────
# 3. The actual problem inputs
# ─────────────────────────────────────────────

# 3a. The current session context JSON (agent must process this)
session_context = {
    "context_window": {
        "used_percentage": 78,
        "tokens_used": 156000,
        "tokens_total": 200000
    },
    "compactions": {
        "count": 2,
        "last_compaction_at": "2024-03-15T11:47:00Z",
        "detected_drops": [
            {"from": 72, "to": 18, "at": "2024-03-15T09:30:00Z"},
            {"from": 68, "to": 12, "at": "2024-03-15T11:47:00Z"}
        ]
    },
    "session_id": "claw-compliance-20240315-b7f2",
    "agent": "compliance-auditor"
}
import json
(WORKSPACE / "session_context.json").write_text(json.dumps(session_context, indent=2))

# 3b. Session notes the agent must snapshot (messy, unstructured)
session_notes = """\
COMPLIANCE AUDIT SESSION NOTES — 2024-03-15
============================================
Started audit of Q1 2024 transaction batch (1,482 records).

[09:15] Identified 12 transactions flagged for manual review due to currency mismatch.
[09:30] Context compaction detected — resumed from checkpoint.
[10:02] DECISION: Escalate transactions above $50,000 to senior compliance officer (per policy CP-204).
[10:45] Modified rules engine config: agents/risk-scanner/config/rules.yaml — added R002 threshold rule.
[11:20] BLOCKER: rate_limit on external sanctions API hit; workaround: cache responses in data/processed/sanctions_cache.json.
[11:47] Second context compaction detected.
[12:05] Next steps: complete review of flagged batch, submit CP-204 escalation report by EOD, fix sanctions API retry logic.
[12:15] NOTE: do not archive Q1 raw data until escalation report is signed off.
"""
(WORKSPACE / "session_notes.txt").write_text(session_notes)

# 3c. Old memory files to test rotation
today = datetime.now().date()

memory_files = {
    today: "## Session Log\n- Normal operation today\n",
    today - timedelta(days=1): "## Session Log\n- Ran nightly audit\n",
    today - timedelta(days=3): "## Session Log\n- Reviewed Q1 batch partial\n",
    today - timedelta(days=8): "## Pre-Compaction Snapshot (old)\n- Archived rule set updated\n",
    today - timedelta(days=14): "## Pre-Compaction Snapshot (very old)\n- Initial agent setup notes\n",
}
for date, content in memory_files.items():
    filepath = WORKSPACE / "memory" / f"{date.isoformat()}.md"
    filepath.write_text(content)

# Adjust mtime for old files so filesystem-based rotation works
import time
for date in memory_files:
    filepath = WORKSPACE / "memory" / f"{date.isoformat()}.md"
    delta_seconds = (today - date).days * 86400
    old_time = time.time() - delta_seconds
    os.utime(filepath, (old_time, old_time))

# ─────────────────────────────────────────────
# 4. The actual scripts (faithfully implementing SKILL.md spec)
# ─────────────────────────────────────────────

# ── context-check.sh ──
context_check_sh = r"""#!/usr/bin/env bash
# context-check.sh — Session health checker
# Usage:
#   bash scripts/context-check.sh                         # human-readable
#   bash scripts/context-check.sh --json                  # JSON output
#   echo '{"context_window":{"used_percentage":72}}' | bash scripts/context-check.sh
#   cat file.json | bash scripts/context-check.sh
# Exit codes: 0=GREEN, 1=YELLOW, 2=RED

set -euo pipefail

HEALTH_GREEN_MAX="${HEALTH_GREEN_MAX:-50}"
HEALTH_RED_MIN="${HEALTH_RED_MIN:-75}"
COMPACTION_DROP="${COMPACTION_DROP:-30}"
SESSION_STATE_FILE="/tmp/session-health-${USER:-default}.json"

JSON_MODE=false
if [[ "${1:-}" == "--json" ]]; then
    JSON_MODE=true
fi

# Read JSON from stdin if available (not a tty), otherwise expect a file arg
INPUT_JSON=""
if [[ ! -t 0 ]]; then
    INPUT_JSON=$(cat)
fi

if [[ -z "$INPUT_JSON" ]]; then
    echo "Error: No JSON input provided. Pipe JSON or use: echo '{...}' | bash scripts/context-check.sh" >&2
    exit 1
fi

# Parse fields
USED_PCT=$(echo "$INPUT_JSON" | jq -r '.context_window.used_percentage // 0')
COMPACTION_COUNT=$(echo "$INPUT_JSON" | jq -r '.compactions.count // 0' 2>/dev/null || echo "0")

# Determine health level
# RED: >=75% OR >=2 compactions
# YELLOW: >=50% OR >=1 compaction
# GREEN: <50% AND 0 compactions
LEVEL="GREEN"
EXIT_CODE=0

if (( $(echo "$USED_PCT >= $HEALTH_RED_MIN" | bc -l) )) || (( COMPACTION_COUNT >= 2 )); then
    LEVEL="RED"
    EXIT_CODE=2
elif (( $(echo "$USED_PCT >= $HEALTH_GREEN_MAX" | bc -l) )) || (( COMPACTION_COUNT >= 1 )); then
    LEVEL="YELLOW"
    EXIT_CODE=1
fi

# Save state
echo "{\"level\":\"$LEVEL\",\"used_pct\":$USED_PCT,\"compactions\":$COMPACTION_COUNT,\"exit_code\":$EXIT_CODE}" \
    > "$SESSION_STATE_FILE"

if $JSON_MODE; then
    echo "{\"level\":\"$LEVEL\",\"used_percentage\":$USED_PCT,\"compactions\":$COMPACTION_COUNT,\"exit_code\":$EXIT_CODE}"
else
    echo "Health Level : $LEVEL"
    echo "Context Used : ${USED_PCT}%"
    echo "Compactions  : ${COMPACTION_COUNT}"
    case "$LEVEL" in
        GREEN)  echo "Status       : Normal operation" ;;
        YELLOW) echo "Status       : Consider saving key facts (snapshot recommended)" ;;
        RED)    echo "Status       : URGENT — Save facts NOW, session ending soon" ;;
    esac
fi

exit $EXIT_CODE
"""
(WORKSPACE / "scripts" / "context-check.sh").write_text(context_check_sh)

# ── snapshot.sh ──
snapshot_sh = r"""#!/usr/bin/env bash
# snapshot.sh — Save key facts to daily memory file
# Usage:
#   bash scripts/snapshot.sh "Fact one" "Fact two" "Fact three"
#   echo -e "Fact one\nFact two" | bash scripts/snapshot.sh -

set -euo pipefail

# Determine memory directory
if [[ -n "${MEMORY_DIR:-}" ]]; then
    MEM_DIR="$MEMORY_DIR"
elif [[ -d "${HOME}/.openclaw/workspace/memory" ]]; then
    MEM_DIR="${HOME}/.openclaw/workspace/memory"
elif [[ -d "${HOME}/.claude/memory" ]]; then
    MEM_DIR="${HOME}/.claude/memory"
else
    # Default to ./memory relative to script location
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    MEM_DIR="${SCRIPT_DIR}/../memory"
fi

mkdir -p "$MEM_DIR"

TODAY=$(date +%Y-%m-%d)
MEM_FILE="${MEM_DIR}/${TODAY}.md"
TIMESTAMP=$(date +%H:%M)

# Collect facts
FACTS=()
if [[ "${1:-}" == "-" ]]; then
    # Read from stdin
    while IFS= read -r line; do
        [[ -n "$line" ]] && FACTS+=("$line")
    done
else
    # Read from arguments
    for arg in "$@"; do
        FACTS+=("$arg")
    done
fi

if [[ ${#FACTS[@]} -eq 0 ]]; then
    echo "Error: No facts provided." >&2
    exit 1
fi

# Write snapshot block
{
    echo ""
    echo "## Pre-Compaction Snapshot (${TIMESTAMP})"
    for fact in "${FACTS[@]}"; do
        echo "- ${fact}"
    done
} >> "$MEM_FILE"

echo "Snapshot saved to: $MEM_FILE (${#FACTS[@]} facts)"
"""
(WORKSPACE / "scripts" / "snapshot.sh").write_text(snapshot_sh)

# ── rotate.sh ──
rotate_sh = r"""#!/usr/bin/env bash
# rotate.sh — Archive old daily memory files
# Usage:
#   bash scripts/rotate.sh                    # Archives files older than 3 days (default)
#   KEEP_DAYS=7 bash scripts/rotate.sh        # Keep 7 days instead

set -euo pipefail

KEEP_DAYS="${KEEP_DAYS:-3}"

# Determine memory directory (same auto-detect as snapshot.sh)
if [[ -n "${MEMORY_DIR:-}" ]]; then
    MEM_DIR="$MEMORY_DIR"
elif [[ -d "${HOME}/.openclaw/workspace/memory" ]]; then
    MEM_DIR="${HOME}/.openclaw/workspace/memory"
elif [[ -d "${HOME}/.claude/memory" ]]; then
    MEM_DIR="${HOME}/.claude/memory"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    MEM_DIR="${SCRIPT_DIR}/../memory"
fi

ARCHIVE_DIR="${MEM_DIR}/archive"
mkdir -p "$ARCHIVE_DIR"

# Find and archive .md files older than KEEP_DAYS
ARCHIVED=0
while IFS= read -r -d '' file; do
    filename=$(basename "$file")
    # Only rotate dated files (YYYY-MM-DD.md pattern)
    if [[ "$filename" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$ ]]; then
        mv "$file" "${ARCHIVE_DIR}/${filename}"
        echo "Archived: $filename"
        ARCHIVED=$((ARCHIVED + 1))
    fi
done < <(find "$MEM_DIR" -maxdepth 1 -name "*.md" -mtime +${KEEP_DAYS} -print0)

echo "Rotation complete. Archived ${ARCHIVED} file(s). Kept files newer than ${KEEP_DAYS} days."
"""
(WORKSPACE / "scripts" / "rotate.sh").write_text(rotate_sh)

# Make scripts executable
for script in ["context-check.sh", "snapshot.sh", "rotate.sh"]:
    p = WORKSPACE / "scripts" / script
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

print("Workspace built successfully.")
print(f"Memory files created: {list((WORKSPACE / 'memory').glob('*.md'))}")