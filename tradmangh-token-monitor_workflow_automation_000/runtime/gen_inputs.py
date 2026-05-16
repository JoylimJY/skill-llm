import os
import stat
import json
import random

random.seed(42)

workspace = "/workspace"

# ── directory structure with distractor files ──────────────────────────────
dirs = [
    "skills/token-monitor/scripts",
    "skills/token-monitor/config",
    "skills/token-monitor/logs",
    "skills/other-skill/scripts",
    "skills/other-skill/config",
    ".openclaw/workspace/skills/token-monitor",
    ".openclaw/workspace/skills/other-skill",
    ".openclaw/bin",
    "projects/ai-gateway/configs",
    "projects/ai-gateway/logs",
    "projects/billing-tracker",
    "docs/runbooks",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ───────────────────────────────────────────────────────
distractors = {
    "skills/other-skill/scripts/run.sh": "#!/bin/bash\necho 'other skill'\n",
    "skills/other-skill/config/settings.json": json.dumps({"enabled": True, "interval": 30}),
    ".openclaw/workspace/skills/other-skill/state.json": json.dumps({"last": "2026-01-01T00:00:00Z"}),
    "projects/ai-gateway/configs/providers.yaml": "providers:\n  - openai-codex\n  - github-copilot\n  - google-antigravity\n",
    "projects/ai-gateway/logs/gateway.log": "2026-02-15 INFO: Request routed to openai-codex\n2026-02-15 INFO: Request routed to github-copilot\n",
    "projects/billing-tracker/costs.json": json.dumps({"month": "2026-02", "total_usd": 412.50}),
    "docs/runbooks/incident-response.md": "# Incident Response\n\nIf quota drops below 10%, escalate to on-call.\n",
    "skills/token-monitor/config/example-threshold.txt": "Suggested threshold: 25%\n(This is just documentation, not a config file the script reads)\n",
    "skills/token-monitor/logs/old-run.log": "[2026-02-14] All quotas OK\n[2026-02-14] openai-codex 5h: 45% left\n",
    ".openclaw/workspace/skills/token-monitor/README.txt": "State file lives here as .token-state.json\n",
    "projects/ai-gateway/configs/routing-rules.json": json.dumps({"fallback": "google-antigravity", "retry": 3}),
    "skills/token-monitor/config/old-config.bak": "QUOTA_THRESHOLD=15\n# deprecated\n",
}
for path, content in distractors.items():
    full = os.path.join(workspace, path)
    with open(full, "w") as f:
        f.write(content)

# ── The two snapshot outputs of `openclaw models status` ──────────────────
# Snapshot 1: initial state (no prior state file)
# openai-codex:  5h=8% (LOW), Day=55% (OK)
# github-copilot: Premium=3% (LOW), Chat=72% (OK)
# google-antigravity: Day=100% (OK), Premium=19% (LOW, just below 20%)
snapshot1 = """\
Provider: openai-codex
  Quota 5h: 8% left
  Quota Day: 55% left

Provider: github-copilot
  Quota Premium: 3% left
  Quota Chat: 72% left

Provider: google-antigravity
  Quota Day: 100% left
  Quota Premium: 19% left
"""

# Snapshot 2: after recovery + new drop
# openai-codex:  5h=45% (RECOVERED), Day=10% (NEW LOW)
# github-copilot: Premium=3% (still low, already warned), Chat=72% (OK)
# google-antigravity: Day=100% (OK), Premium=19% (still low, already warned)
snapshot2 = """\
Provider: openai-codex
  Quota 5h: 45% left
  Quota Day: 10% left

Provider: github-copilot
  Quota Premium: 3% left
  Quota Chat: 72% left

Provider: google-antigravity
  Quota Day: 100% left
  Quota Premium: 19% left
"""

with open(os.path.join(workspace, ".openclaw/bin/snapshot1.txt"), "w") as f:
    f.write(snapshot1)

with open(os.path.join(workspace, ".openclaw/bin/snapshot2.txt"), "w") as f:
    f.write(snapshot2)

# ── The real check-quota.sh script (as per SKILL.md spec) ─────────────────
# We write this so the agent has the actual script to invoke.
check_quota_sh = r"""#!/usr/bin/env bash
# token-monitor/scripts/check-quota.sh
# Monitors OpenClaw token/quota usage and alerts when below threshold.

set -euo pipefail

THRESHOLD="${QUOTA_THRESHOLD:-20}"
STATE_FILE="${QUOTA_STATE_FILE:-$HOME/.openclaw/workspace/skills/token-monitor/.token-state.json}"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --threshold)
      THRESHOLD="$2"
      shift 2
      ;;
    --state-file)
      STATE_FILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

# Ensure state directory exists
mkdir -p "$(dirname "$STATE_FILE")"

# Run openclaw models status
RAW_OUTPUT=$(openclaw models status 2>/dev/null)

# Parse all quotas: extract "Provider: X" and "Quota Y: Z% left"
declare -A CURRENT_MAP
CURRENT_PROVIDER=""
while IFS= read -r line; do
  if [[ "$line" =~ ^Provider:\ (.+)$ ]]; then
    CURRENT_PROVIDER="${BASH_REMATCH[1]}"
  elif [[ "$line" =~ Quota\ ([^:]+):\ ([0-9]+)%\ left ]]; then
    QUOTA_NAME="${BASH_REMATCH[1]}"
    QUOTA_PCT="${BASH_REMATCH[2]}"
    CURRENT_MAP["${CURRENT_PROVIDER}:${QUOTA_NAME}"]="$QUOTA_PCT"
  fi
done <<< "$RAW_OUTPUT"

# Build current array for state
CURRENT_ARRAY=()
for key in "${!CURRENT_MAP[@]}"; do
  CURRENT_ARRAY+=("${key}=${CURRENT_MAP[$key]}")
done

# Load previous state
PREV_WARNED=()
if [[ -f "$STATE_FILE" ]]; then
  mapfile -t PREV_WARNED < <(jq -r '.warned[]' "$STATE_FILE" 2>/dev/null || true)
fi

# Identify low quotas
LOW_QUOTAS=()
for key in "${!CURRENT_MAP[@]}"; do
  pct="${CURRENT_MAP[$key]}"
  if (( pct < THRESHOLD )); then
    provider="${key%%:*}"
    quota="${key##*:}"
    LOW_QUOTAS+=("${provider} ${quota}: ${pct}% left")
  fi
done

# Determine new warnings (low now, not in prev warned)
NEW_WARNINGS=()
for item in "${LOW_QUOTAS[@]}"; do
  found=0
  for prev in "${PREV_WARNED[@]}"; do
    if [[ "$prev" == "$item" ]]; then
      found=1
      break
    fi
  done
  if (( found == 0 )); then
    NEW_WARNINGS+=("$item")
  fi
done

# Determine recoveries (was warned, now OK)
RECOVERIES=()
for prev in "${PREV_WARNED[@]}"; do
  found=0
  for low in "${LOW_QUOTAS[@]}"; do
    if [[ "$low" == "$prev" ]]; then
      found=1
      break
    fi
  done
  if (( found == 0 )); then
    RECOVERIES+=("$prev")
  fi
done

# Build new warned list: prev warned minus recovered, plus new warnings
NEW_WARNED=()
for prev in "${PREV_WARNED[@]}"; do
  recovered=0
  for rec in "${RECOVERIES[@]}"; do
    if [[ "$rec" == "$prev" ]]; then
      recovered=1
      break
    fi
  done
  if (( recovered == 0 )); then
    NEW_WARNED+=("$prev")
  fi
done
for new in "${NEW_WARNINGS[@]}"; do
  NEW_WARNED+=("$new")
done

# Send alerts
ALERT_TEXT=""
if (( ${#NEW_WARNINGS[@]} > 0 )); then
  ALERT_TEXT="⚠️ Model Quota Alert (<${THRESHOLD}%):"$'\n'
  for w in "${NEW_WARNINGS[@]}"; do
    ALERT_TEXT+="• ${w}"$'\n'
  done
fi

if (( ${#RECOVERIES[@]} > 0 )); then
  ALERT_TEXT+="✅ Quota Recovered (>=${THRESHOLD}%):"$'\n'
  for r in "${RECOVERIES[@]}"; do
    ALERT_TEXT+="• ${r}"$'\n'
  done
fi

if [[ -n "$ALERT_TEXT" ]]; then
  echo "$ALERT_TEXT"
  openclaw cron wake --text "$ALERT_TEXT" --mode now 2>/dev/null || true
fi

# Build JSON for state file
CURRENT_JSON=$(printf '%s\n' "${CURRENT_ARRAY[@]}" | jq -R . | jq -s .)
WARNED_JSON=$(printf '%s\n' "${NEW_WARNED[@]}" | jq -R . | jq -s .)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jq -n \
  --argjson warned "$WARNED_JSON" \
  --argjson current "$CURRENT_JSON" \
  --arg lastCheck "$TIMESTAMP" \
  --argjson threshold "$THRESHOLD" \
  '{warned: $warned, current: $current, lastCheck: $lastCheck, threshold: $threshold}' \
  > "$STATE_FILE"
"""

script_path = os.path.join(workspace, "skills/token-monitor/scripts/check-quota.sh")
with open(script_path, "w") as f:
    f.write(check_quota_sh)
os.chmod(script_path, 0o755)

print("Workspace generated successfully.")
print(f"Snapshot1 at: {workspace}/.openclaw/bin/snapshot1.txt")
print(f"Snapshot2 at: {workspace}/.openclaw/bin/snapshot2.txt")
print(f"Script at: {workspace}/skills/token-monitor/scripts/check-quota.sh")