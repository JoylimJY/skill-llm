import os
import json
import random
import sys
from pathlib import Path

random.seed(42)

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
base = Path(workspace)

# --- Create realistic, deeply nested directory structure ---
dirs = [
    "scripts",
    "config",
    "config/backup",
    "logs",
    "logs/gateway",
    "logs/bots",
    "services/gateway",
    "services/auth",
    "services/nlp",
    "docs/internal",
    "docs/api",
    "tools/monitoring",
    "tools/deploy",
    "archive/2023",
    "archive/2024",
]
for d in dirs:
    (base / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "docs/internal/bot_policy.txt": "All bots must comply with data governance policy v2.3.",
    "docs/internal/onboarding.md": "# Onboarding\nSee IT for access credentials.",
    "docs/api/gateway_api.txt": "GET /api/v1/status\nPOST /api/v1/restart",
    "logs/gateway/gateway.log": "[2024-01-10 08:00:00] Gateway started.\n[2024-01-10 08:01:00] Bot registered: bot-legacy-001\n",
    "logs/bots/bot_errors.log": "[ERROR] 2024-01-09 bot-alpha: timeout after 30s\n[ERROR] 2024-01-09 bot-beta: auth failure\n",
    "services/gateway/config_template.json": json.dumps({"version": "1.0", "bots": []}, indent=2),
    "services/auth/auth_config.yaml": "auth:\n  provider: ldap\n  host: ldap.internal\n",
    "services/nlp/model_registry.json": json.dumps({"models": ["glm-4", "baidu-ernie", "qwen-max"]}, indent=2),
    "tools/monitoring/check_bots.sh": "#!/bin/bash\necho 'Checking bots...'\n",
    "tools/deploy/deploy.sh": "#!/bin/bash\necho 'Deploying services...'\n",
    "archive/2023/old_config.json": json.dumps({"bots": [{"id": "deprecated-bot-x"}]}, indent=2),
    "archive/2024/migration_notes.txt": "Migrated 3 bots from v1 to v2 format on 2024-03-15.",
    "config/backup/.gitkeep": "",
    "tools/monitoring/metrics.json": json.dumps({"uptime": "99.8%", "requests": 48201}, indent=2),
}
for rel_path, content in distractor_files.items():
    p = base / rel_path
    p.write_text(content)

# --- The real config file: openclaw.json ---
# Pre-seeded with 2 bots: one to be deleted, one to be updated
openclaw_config = {
    "gateway": {
        "port": 8080,
        "logLevel": "info"
    },
    "bots": [
        {
            "botId": "bot-deprecated-q2",
            "appId": "cli_old_deprecated_001",
            "appSecret": "OLD_SECRET_DEPRECATED_XYZ",
            "model": "bailian-coding-plan/glm-5"
        },
        {
            "botId": "bot-sales-assistant",
            "appId": "cli_sales_20240101",
            "appSecret": "SECRET_SALES_AAABBB",
            "model": "glm-4-flash"
        }
    ]
}
config_path = base / "config" / "openclaw.json"
config_path.write_text(json.dumps(openclaw_config, indent=2))

# --- The feishu-bot.sh script ---
# This is the actual mock script that implements the SKILL.md logic
script_content = r"""#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$BASE_DIR/config/openclaw.json"
GATEWAY_RESTART_MARKER="$BASE_DIR/logs/gateway/restart_called"

# Backup function: creates backup with UTC+8 timestamp
backup_config() {
    # Simulate UTC+8 by adding 8 hours to UTC
    local ts
    ts=$(TZ="Asia/Shanghai" date "+%Y.%m%d.%H%M" 2>/dev/null || \
         date -u "+%Y.%m%d.%H%M")
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak.${ts}"
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
  add)
    BOT_ID=""
    APP_ID=""
    APP_SECRET=""
    MODEL="bailian-coding-plan/glm-5"
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --botId) BOT_ID="$2"; shift 2 ;;
        --appId) APP_ID="$2"; shift 2 ;;
        --appSecret) APP_SECRET="$2"; shift 2 ;;
        --model) MODEL="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
      esac
    done
    [[ -z "$BOT_ID" || -z "$APP_ID" || -z "$APP_SECRET" ]] && { echo "Missing required args for add"; exit 1; }
    # Check if bot already exists
    EXISTS=$(jq --arg id "$BOT_ID" '[.bots[] | select(.botId == $id)] | length' "$CONFIG_FILE")
    [[ "$EXISTS" -gt 0 ]] && { echo "Bot $BOT_ID already exists"; exit 1; }
    backup_config
    TMP=$(mktemp)
    jq --arg id "$BOT_ID" --arg aid "$APP_ID" --arg asec "$APP_SECRET" --arg model "$MODEL" \
      '.bots += [{"botId": $id, "appId": $aid, "appSecret": $asec, "model": $model}]' \
      "$CONFIG_FILE" > "$TMP" && mv "$TMP" "$CONFIG_FILE"
    echo "Bot $BOT_ID added successfully."
    ;;
  delete)
    BOT_ID=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --botId) BOT_ID="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
      esac
    done
    [[ -z "$BOT_ID" ]] && { echo "Missing --botId"; exit 1; }
    backup_config
    TMP=$(mktemp)
    jq --arg id "$BOT_ID" '.bots = [.bots[] | select(.botId != $id)]' \
      "$CONFIG_FILE" > "$TMP" && mv "$TMP" "$CONFIG_FILE"
    echo "Bot $BOT_ID deleted successfully."
    ;;
  update)
    BOT_ID=""
    MODEL=""
    APP_ID=""
    APP_SECRET=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --botId) BOT_ID="$2"; shift 2 ;;
        --model) MODEL="$2"; shift 2 ;;
        --appId) APP_ID="$2"; shift 2 ;;
        --appSecret) APP_SECRET="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
      esac
    done
    [[ -z "$BOT_ID" ]] && { echo "Missing --botId"; exit 1; }
    backup_config
    TMP=$(mktemp)
    CONFIG=$(cat "$CONFIG_FILE")
    if [[ -n "$MODEL" ]]; then
      CONFIG=$(echo "$CONFIG" | jq --arg id "$BOT_ID" --arg val "$MODEL" \
        '(.bots[] | select(.botId == $id) | .model) = $val')
    fi
    if [[ -n "$APP_ID" ]]; then
      CONFIG=$(echo "$CONFIG" | jq --arg id "$BOT_ID" --arg val "$APP_ID" \
        '(.bots[] | select(.botId == $id) | .appId) = $val')
    fi
    if [[ -n "$APP_SECRET" ]]; then
      CONFIG=$(echo "$CONFIG" | jq --arg id "$BOT_ID" --arg val "$APP_SECRET" \
        '(.bots[] | select(.botId == $id) | .appSecret) = $val')
    fi
    echo "$CONFIG" > "$CONFIG_FILE"
    echo "Bot $BOT_ID updated successfully."
    ;;
  list)
    echo "=== Feishu Bots ==="
    jq -r '.bots[] | "[\(.botId)] appId=\(.appId) model=\(.model)"' "$CONFIG_FILE"
    ;;
  info)
    BOT_ID=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --botId) BOT_ID="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
      esac
    done
    [[ -z "$BOT_ID" ]] && { echo "Missing --botId"; exit 1; }
    jq --arg id "$BOT_ID" '.bots[] | select(.botId == $id)' "$CONFIG_FILE"
    ;;
  *)
    echo "Usage: feishu-bot.sh {add|delete|update|list|info} [args...]"
    exit 1
    ;;
esac
"""

script_path = base / "scripts" / "feishu-bot.sh"
script_path.write_text(script_content)

# --- Mock openclaw gateway restart command ---
gateway_script = r"""#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
MARKER="$BASE_DIR/logs/gateway/restart_called"
echo "Gateway restarted at $(date)" >> "$MARKER"
echo "openclaw gateway restarted successfully."
"""
openclaw_bin = base / "scripts" / "openclaw"
openclaw_bin.write_text(gateway_script)

print(f"Workspace initialized at: {workspace}")
print(f"Config: {config_path}")
print(f"Script: {script_path}")