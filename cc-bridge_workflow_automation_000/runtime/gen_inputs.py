#!/usr/bin/env python3
"""
Generates the sandbox workspace for the cc-bridge routing task.
"""
import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure (distractors) ─────────────────────────────────────────
dirs = [
    ".openclaw/workspace/skills/cc-bridge/scripts",
    ".openclaw/workspace/skills/cc-bridge/references",
    ".openclaw/workspace/skills/other-skill/scripts",
    ".openclaw/config",
    ".openclaw/logs",
    "project/src/modules",
    "project/src/utils",
    "project/tests",
    "project/docs",
    "vendor/openclaw-sdk/lib",
    "vendor/openclaw-sdk/examples",
    "tmp/sessions",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractor_files = {
    ".openclaw/config/channels.yaml": """\
channels:
  - name: telegram
    token: REDACTED
  - name: qq
    token: REDACTED
""",
    ".openclaw/config/agent.yaml": """\
agent:
  name: openclaw-dev
  version: 0.2.1
  skills:
    - cc-bridge
    - weather
""",
    ".openclaw/logs/agent.log": "\n".join(
        f"[2024-01-{i:02d}] INFO session started" for i in range(1, 12)
    ),
    ".openclaw/workspace/skills/other-skill/scripts/other.sh": "#!/bin/bash\necho 'other skill'",
    ".openclaw/workspace/skills/cc-bridge/references/usage.md": """\
# CC Bridge Usage

Use /cc start to begin a Claude Code session.
Use /cc stop to end the session.
""",
    "project/src/modules/router.py": """\
# placeholder router module
def route(msg): pass
""",
    "project/src/utils/helpers.py": """\
def sanitize(s): return s
""",
    "project/tests/test_router.py": """\
import pytest
def test_placeholder(): assert True
""",
    "project/docs/api.md": "# API Documentation\nTBD",
    "vendor/openclaw-sdk/lib/sdk.py": "# SDK stub",
    "vendor/openclaw-sdk/examples/example_agent.py": "# example agent stub",
    "tmp/sessions/.gitkeep": "",
}
for rel, content in distractor_files.items():
    p = WORKSPACE / rel
    p.write_text(content)

# ── Mock cc-bridge.sh ──────────────────────────────────────────────────────────
# This mock records every invocation to a call_log.jsonl file and returns
# scripted responses based on the call sequence / action.

mock_script = r"""#!/bin/bash
# Mock cc-bridge.sh for evaluation purposes
# Usage: cc-bridge.sh <SESSION_ID> <ACTION> [ARG] [--long]

SESSION_ID="$1"
ACTION="$2"
ARG="$3"
FLAG="$4"

LOG_FILE="/workspace/tmp/sessions/call_log.jsonl"
COUNTER_FILE="/workspace/tmp/sessions/call_counter.txt"

# Read and increment call counter
if [ ! -f "$COUNTER_FILE" ]; then
    echo "0" > "$COUNTER_FILE"
fi
COUNT=$(cat "$COUNTER_FILE")
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# Build JSON log entry
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_ENTRY="{\"call_n\": $COUNT, \"session_id\": \"$SESSION_ID\", \"action\": \"$ACTION\", \"arg\": \"$ARG\", \"flag\": \"$FLAG\", \"ts\": \"$TIMESTAMP\"}"
echo "$LOG_ENTRY" >> "$LOG_FILE"

# Scripted responses based on call number and action
case "$ACTION" in
  status)
    case "$COUNT" in
      1) echo "⭕ 没有活跃" ;;
      # After start (call 2 was start), call 3 is status → active
      3) echo "✅ Claude Code 会话运行中" ;;
      # call 5 is status before sending large task → active
      5) echo "✅ Claude Code 会话运行中" ;;
      # call 7 is status before approval message → waiting
      7) echo "⚠️  CC 正在等待审批" ;;
      # call 9 is status before cc slash command → active
      9) echo "✅ Claude Code 会话运行中" ;;
      # call 11 is status before stop command → active
      11) echo "✅ Claude Code 会话运行中" ;;
      *) echo "✅ Claude Code 会话运行中" ;;
    esac
    ;;
  start)
    echo "✅ Claude Code 会话已启动"
    ;;
  send)
    if [ "$FLAG" = "--long" ]; then
      # Simulate long task response
      echo "🤖 CC is refactoring... done. Created 15 files across src/ directory."
    else
      echo "Hello from Claude Code. File analysis complete."
    fi
    ;;
  approve)
    echo "✅ 审批已发送: option $ARG"
    ;;
  stop)
    echo "⭕ Claude Code 会话已停止"
    ;;
  peek)
    echo "Current terminal: Claude Code v1.2 - Waiting for input"
    ;;
  history)
    # Generate output > 3000 chars to test truncation
    python3 -c "
lines = []
for i in range(200):
    lines.append(f'[Line {i:03d}] Processing file_{i:03d}.py - analysis complete, no issues found in module.')
print('\n'.join(lines))
"
    ;;
  *)
    echo "Unknown action: $ACTION"
    exit 1
    ;;
esac
"""

script_path = WORKSPACE / ".openclaw/workspace/skills/cc-bridge/scripts/cc-bridge.sh"
script_path.write_text(mock_script)
script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Input messages JSON ────────────────────────────────────────────────────────
# The agent must process these messages in sequence.
# Channel: "telegram-group" (hyphen must be sanitized → underscore or removed)
# chat_id: "chat#42!main" (special chars must be sanitized → only [a-zA-Z0-9_])
# Expected session_id: "telegramgroup_chat42main" or similar (strip non-alphanum except _)
# Actually per SKILL.md: use only [a-zA-Z0-9_]
# "telegram-group" → "telegram_group" (replace - with _) ... but SKILL.md says
# "using only [a-zA-Z0-9_]" — agent must decide how to handle hyphen.
# We accept: replace non-[a-zA-Z0-9] with _ OR strip them.
# The eval will check the session_id used is consistent and sanitized.

messages = [
    {
        "msg_id": 1,
        "channel": "telegram-group",
        "chat_id": "chat#42!main",
        "text": "start claude code",
        "note": "CC control: start. Status first → off. Then start."
    },
    {
        "msg_id": 2,
        "channel": "telegram-group",
        "chat_id": "chat#42!main",
        "text": "cc状态",
        "note": "CC control: status check while active."
    },
    {
        "msg_id": 3,
        "channel": "telegram-group",
        "chat_id": "chat#42!main",
        "text": "帮我重构整个项目的所有模块，写完整的测试覆盖",
        "note": "Large task → must use --long flag. Status first → active. Then send with --long."
    },
    {
        "msg_id": 4,
        "channel": "telegram-group",
        "chat_id": "chat#42!main",
        "text": "允许",
        "note": "Approval: '允许' → approve 2 (Allow always). Status first → waiting."
    },
    {
        "msg_id": 5,
        "channel": "telegram-group",
        "chat_id": "chat#42!main",
        "text": "/compact",
        "note": "CC slash command passthrough → send '/compact'. Status first → active."
    },
    {
        "msg_id": 6,
        "channel": "telegram-group",
        "chat_id": "chat#42!main",
        "text": "stop claude code",
        "note": "CC control: stop. Status first → active. Then stop."
    },
]

(WORKSPACE / "incoming_messages.json").write_text(
    json.dumps(messages, ensure_ascii=False, indent=2)
)

# ── Task spec ──────────────────────────────────────────────────────────────────
# (Not a README — just the raw input data the agent needs to process)
# The agent should write message_handler.py and routing_log.json

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in WORKSPACE.rglob('*') if _.is_file())}")