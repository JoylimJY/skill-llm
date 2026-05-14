import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"

# ── Directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "skills/context-sentinel/scripts",
    "skills/context-sentinel/docs",
    "skills/memory-vault/scripts",
    "skills/memory-vault/docs",
    "skills/token-optimizer/scripts",
    "agent/heartbeat",
    "agent/logs",
    "agent/config",
    "agent/sessions",
    "ops/monitoring",
    "ops/alerts",
    "ops/reports",
    "tmp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "agent/config/agent_config.yaml": """\
agent_id: sentinel-agent-001
version: 2.3.1
max_retries: 3
timeout_seconds: 30
log_level: INFO
models:
  primary: opus-4.6
  fallback: opus-4.5
  economy: gemini-2.5-pro
""",
    "agent/heartbeat/HEARTBEAT.md": """\
# Heartbeat Checklist
1. Check network connectivity.
2. Verify session token validity.
3. Run context sentinel (see skills/context-sentinel).
4. Log results to agent/logs/.
""",
    "agent/sessions/session_meta.json": """\
{
  "session_id": "sess-20240712-alpha",
  "started_at": "2024-07-12T08:00:00Z",
  "owner": "orchestrator-v2"
}
""",
    "agent/logs/previous_run.log": """\
2024-07-12T08:01:00Z [INFO] Heartbeat executed.
2024-07-12T08:01:01Z [INFO] Context check: STATUS_OK
2024-07-12T08:31:00Z [INFO] Heartbeat executed.
2024-07-12T08:31:02Z [INFO] Context check: STATUS_OK
""",
    "ops/monitoring/thresholds.json": """\
{
  "warning_pct": 70,
  "critical_pct": 80,
  "emergency_pct": 95
}
""",
    "ops/alerts/alert_rules.yaml": """\
rules:
  - name: high_context
    condition: context_pct > 80
    severity: WARNING
    action: notify_ops_team
  - name: critical_context
    condition: context_pct > 95
    severity: CRITICAL
    action: emergency_handoff
""",
    "ops/reports/.gitkeep": "",
    "skills/memory-vault/docs/README.txt": """\
Memory Vault Skill - v0.9.2
Manages persistent key-value memory across sessions.
See scripts/ for implementation details.
""",
    "skills/memory-vault/scripts/flush_memory.sh": """\
#!/bin/bash
# Flush memory vault to disk
echo "Memory flushed at $(date)"
""",
    "skills/token-optimizer/scripts/compress.py": """\
#!/usr/bin/env python3
# Compresses conversation history to reduce token usage.
import sys
print(f"Compressing history: {sys.argv[1] if len(sys.argv) > 1 else 'default'}")
""",
    "skills/context-sentinel/docs/MEMORY.md": """\
# MEMORY.md - Cascading Model Protocol

## Model Cascade Order

| Step | Model         | Context Threshold | Next Action               |
|------|---------------|-------------------|---------------------------|
| 1    | Opus 4.6      | 80%               | Switch to Opus 4.5        |
| 2    | Opus 4.5      | 80%               | Switch to Gemini 2.5 Pro  |
| 3    | Gemini 2.5 Pro| 80%               | Trigger HANDOFF           |

## Notes
- Thresholds are HARD limits. Do not exceed without explicit override.
- Handoff process writes to handoff_request.txt in agent/sessions/.
- Model IDs must match exactly: opus-4.6, opus-4.5, gemini-2.5-pro
""",
    "tmp/scratch/old_check.sh": """\
#!/bin/bash
# DEPRECATED: Use check_context.ps1 instead
echo "This script is no longer maintained."
exit 1
""",
    "agent/config/model_ids.txt": """\
# Canonical model identifiers (do NOT use aliases)
opus-4.6
opus-4.5
gemini-2.5-pro
""",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# Make distractor shell script executable
os.chmod(os.path.join(workspace, "skills/memory-vault/scripts/flush_memory.sh"), 0o755)
os.chmod(os.path.join(workspace, "tmp/scratch/old_check.sh"), 0o755)

# ── THE PROBLEM: session_state.json ──────────────────────────────────────────
# Opus 4.5 at 85% context → should trigger SWITCH_TO:gemini-2.5-pro
session_state = {
    "current_model": "opus-4.5",
    "context_pct": 85,
    "session_id": "sess-20240712-alpha",
    "tokens_used": 174080,
    "tokens_max": 204800,
    "last_heartbeat": "2024-07-12T09:14:33Z"
}
with open(os.path.join(workspace, "session_state.json"), "w") as f:
    json.dump(session_state, f, indent=2)

# ── THE SENTINEL SCRIPT: check_context.ps1 ───────────────────────────────────
# This script already "exists" as part of the skill; we provision it here.
check_context_ps1 = r'''# Context Sentinel - check_context.ps1
# Reads session_state.json and outputs the required action per the Cascading Model Protocol.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$stateFile = Join-Path $workspaceRoot "session_state.json"

if (-not (Test-Path $stateFile)) {
    Write-Error "session_state.json not found at: $stateFile"
    exit 1
}

$state = Get-Content $stateFile | ConvertFrom-Json
$model = $state.current_model
$ctxPct = [int]$state.context_pct

# Cascading Model Protocol
if ($model -eq "opus-4.6") {
    if ($ctxPct -ge 80) {
        Write-Output "SWITCH_TO:opus-4.5"
    } else {
        Write-Output "STATUS_OK"
    }
} elseif ($model -eq "opus-4.5") {
    if ($ctxPct -ge 80) {
        Write-Output "SWITCH_TO:gemini-2.5-pro"
    } else {
        Write-Output "STATUS_OK"
    }
} elseif ($model -eq "gemini-2.5-pro") {
    if ($ctxPct -ge 80) {
        Write-Output "HANDOFF_NOW"
    } else {
        Write-Output "STATUS_OK"
    }
} else {
    Write-Output "STATUS_OK"
}
'''

ps1_path = os.path.join(workspace, "skills/context-sentinel/scripts/check_context.ps1")
with open(ps1_path, "w") as f:
    f.write(check_context_ps1)

# ── MOCK: session_status command ──────────────────────────────────────────────
# The SKILL.md says: run `session_status model=<model_id>` for a SWITCH_TO action.
# We mock this as an executable script in /usr/local/bin so the agent can call it naturally.
session_status_script = """\
#!/bin/bash
# Mock session_status command
# Usage: session_status model=<model_id>
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$TIMESTAMP [session_status] Called with args: $@" >> /workspace/agent/logs/session_status_calls.log
for arg in "$@"; do
    if [[ "$arg" == model=* ]]; then
        MODEL_ID="${arg#model=}"
        echo "$TIMESTAMP [session_status] Model switch recorded: $MODEL_ID" >> /workspace/agent/logs/session_status_calls.log
        # Update session_state.json to reflect the model switch
        python3 -c "
import json, sys
with open('/workspace/session_state.json', 'r') as f:
    s = json.load(f)
s['switched_to'] = '$MODEL_ID'
with open('/workspace/session_state.json', 'w') as f:
    json.dump(s, f, indent=2)
"
    fi
done
echo "session_status: acknowledged"
"""

# Write to a temp location; setup_script will move it to /usr/local/bin
session_status_path = os.path.join(workspace, "tmp/session_status_mock.sh")
with open(session_status_path, "w") as f:
    f.write(session_status_script)
os.chmod(session_status_path, 0o755)

print("Workspace generation complete.")
print(f"  session_state.json: opus-4.5 at 85% context")
print(f"  check_context.ps1 provisioned at skills/context-sentinel/scripts/")
print(f"  session_status mock ready at tmp/session_status_mock.sh")