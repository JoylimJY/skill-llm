#!/usr/bin/env python3
import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────

dirs = [
    "skills/dreaming/scripts",
    "skills/summarizer/scripts",
    "skills/planner/scripts",
    "data",
    "memory/dreams",
    "memory/notes",
    "memory/archive",
    "logs",
    "config",
    "docs",
    "scripts",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────

distractor_files = {
    "skills/summarizer/scripts/summarize.sh": "#!/bin/bash\necho 'summarizing...'\n",
    "skills/planner/scripts/plan.sh": "#!/bin/bash\necho 'planning...'\n",
    "logs/heartbeat-2026-07-10.log": "HEARTBEAT_OK\nHEARTBEAT_OK\nHEARTBEAT_OK\n",
    "logs/heartbeat-2026-07-11.log": "HEARTBEAT_OK\nNO_DREAM\nHEARTBEAT_OK\n",
    "config/heartbeat.conf": "interval=60\nmode=quiet\n",
    "config/agent.conf": "agent_id=pharma-research-bot\nversion=2.1.0\n",
    "docs/workflow.md": "# Workflow\nThis agent runs overnight tasks.\n",
    "docs/architecture.md": "# Architecture\nHeartbeat loop -> skill dispatch -> state update\n",
    "memory/notes/todo.md": "- [ ] Review compound library results\n- [ ] Update IC50 analysis\n",
    "memory/archive/old-dream-2026-01-15.md": "# Old Dream\nSome past reflection content.\n",
    "scripts/run-heartbeat.sh": "#!/bin/bash\necho 'heartbeat running'\n",
    "skills/dreaming/scripts/README.txt": "This directory contains the dreaming skill scripts.\n",
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.write_text(content)

# ── CORRUPTED dream-state.json (agent must fix it) ───────────────────────────
# Wrong fields: missing maxDreamsPerNight, wrong dreamChance type (string), wrong field name
bad_state = {
    "last_dream": "2020-01-01",        # wrong field name (should be lastDreamDate)
    "dreams_tonight": 0,               # wrong field name (should be dreamsTonight)
    "dream_chance": "sometimes",       # wrong type and field name (should be dreamChance float)
    # maxDreamsPerNight is missing entirely
}
(WORKSPACE / "data/dream-state.json").write_text(json.dumps(bad_state, indent=2))

# ── Stale / irrelevant dream-config stub (wrong format, agent must replace) ──
bad_config = {
    "dream_topics": [
        {"id": 1, "text": "think about something"},
        {"id": 2, "text": "another vague idea"},
    ]
}
(WORKSPACE / "data/dream-config.json").write_text(json.dumps(bad_config, indent=2))

# ── should-dream.sh ──────────────────────────────────────────────────────────
# Realistic implementation that:
#  - Always passes quiet-hours check (QUIET_START=0, QUIET_END=24 → always quiet)
#  - Reads dream-state.json for dreamChance and dreamsTonight/maxDreamsPerNight
#  - Reads dream-config.json for topics if present (correct format)
#  - Rolls dice, selects topic, prints "category:prompt", updates state
should_dream_sh = r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${WORKSPACE:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

STATE_FILE="$WORKSPACE/data/dream-state.json"
CONFIG_FILE="$WORKSPACE/data/dream-config.json"

# Quiet hours: always active (00:00 – 24:00) so sandbox tests always pass
QUIET_START=0
QUIET_END=24

CURRENT_HOUR=$(date +%H | sed 's/^0//')
CURRENT_HOUR=${CURRENT_HOUR:-0}

# Check quiet hours
if [ "$CURRENT_HOUR" -ge "$QUIET_START" ] && [ "$CURRENT_HOUR" -lt "$QUIET_END" ]; then
    : # within quiet hours
else
    exit 1
fi

# Read state
if [ ! -f "$STATE_FILE" ]; then
    echo "ERROR: $STATE_FILE not found" >&2
    exit 1
fi

LAST_DATE=$(jq -r '.lastDreamDate // ""' "$STATE_FILE")
DREAMS_TONIGHT=$(jq -r '.dreamsTonight // 0' "$STATE_FILE")
MAX_DREAMS=$(jq -r '.maxDreamsPerNight // 1' "$STATE_FILE")
DREAM_CHANCE=$(jq -r '.dreamChance // 1.0' "$STATE_FILE")
TODAY=$(date +%Y-%m-%d)

# Reset nightly counter if new day
if [ "$LAST_DATE" != "$TODAY" ]; then
    DREAMS_TONIGHT=0
fi

# Check nightly limit
if [ "$DREAMS_TONIGHT" -ge "$MAX_DREAMS" ]; then
    exit 2
fi

# Roll dice against dreamChance using python3
ROLL=$(python3 -c "import random; random.seed(); print('1' if random.random() < $DREAM_CHANCE else '0')")
if [ "$ROLL" != "1" ]; then
    exit 3
fi

# Load topics
DEFAULT_TOPICS=(
    "future:What could this research direction become in 10 years?"
    "tangent:An interesting technique from another field worth exploring"
    "strategy:Long-term thinking about research prioritization"
    "creative:A wild hypothesis that might be crazy or brilliant"
    "reflection:Looking back at recent experimental results"
    "hypothetical:What if a key assumption in this domain is wrong?"
    "connection:Unexpected links between two research areas"
)

TOPICS=()

if [ -f "$CONFIG_FILE" ]; then
    # Read topics array from config — expects array of "category:prompt" strings
    TOPIC_COUNT=$(jq '.topics | length' "$CONFIG_FILE" 2>/dev/null || echo 0)
    if [ "$TOPIC_COUNT" -gt 0 ]; then
        while IFS= read -r line; do
            TOPICS+=("$line")
        done < <(jq -r '.topics[]' "$CONFIG_FILE")
    fi
fi

if [ "${#TOPICS[@]}" -eq 0 ]; then
    TOPICS=("${DEFAULT_TOPICS[@]}")
fi

# Select random topic
TOPIC_COUNT="${#TOPICS[@]}"
IDX=$(python3 -c "import random; print(random.randint(0, $TOPIC_COUNT - 1))")
SELECTED="${TOPICS[$IDX]}"

# Update state
NEW_DREAMS=$((DREAMS_TONIGHT + 1))
jq --arg date "$TODAY" --argjson d "$NEW_DREAMS" \
    '.lastDreamDate = $date | .dreamsTonight = $d' \
    "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"

echo "$SELECTED"
"""

sd_path = WORKSPACE / "skills/dreaming/scripts/should-dream.sh"
sd_path.write_text(should_dream_sh)
sd_path.chmod(sd_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

print("Workspace generated successfully.")
print(f"  data/dream-state.json: CORRUPTED (wrong field names)")
print(f"  data/dream-config.json: WRONG FORMAT (needs replacement)")
print(f"  skills/dreaming/scripts/should-dream.sh: created")