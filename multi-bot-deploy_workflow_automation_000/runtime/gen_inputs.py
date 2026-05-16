#!/usr/bin/env python3
import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Create distractor directory structure ──────────────────────────────────────
dirs = [
    "docs/architecture",
    "docs/api",
    "internal/bots/legacy",
    "internal/bots/archive",
    "internal/channels/wechat",
    "internal/channels/slack",
    "scripts/maintenance",
    "scripts/backup",
    "config/templates",
    "config/old",
    "logs/2024",
    "logs/2025",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractor_files = {
    "docs/architecture/system_overview.md": "# System Overview\nMulti-tenant bot platform.\n",
    "docs/api/feishu_api_notes.txt": "Feishu API base URL: https://open.feishu.cn/open-apis\nRate limit: 50 req/s\n",
    "internal/bots/legacy/old_bot_config.json": json.dumps({
        "botName": "OldSupportBot",
        "channel": "feishu",
        "appId": "cli_legacy001",
        "appSecret": "legacy_secret_abc"
    }, indent=2),
    "internal/bots/archive/retired_marketing_bot.json": json.dumps({
        "agentId": "marketing-old",
        "status": "retired",
        "retiredAt": "2024-06-01"
    }, indent=2),
    "internal/channels/wechat/wechat_config_template.json": json.dumps({
        "channel": "wechat",
        "corpId": "wx_xxx",
        "corpSecret": "secret_xxx"
    }, indent=2),
    "internal/channels/slack/slack_setup_notes.txt": "Slack channel setup requires OAuth 2.0 bot token.\nScopes: chat:write, channels:read\n",
    "scripts/maintenance/cleanup_old_agents.sh": "#!/bin/bash\n# Remove agents older than 90 days\necho 'Cleanup script placeholder'\n",
    "scripts/backup/backup_config.sh": "#!/bin/bash\n# Manual backup script\ncp ~/.openclaw/openclaw.json ~/backups/openclaw_$(date +%Y%m%d).json\n",
    "config/templates/agent_template.yaml": "agentId: PLACEHOLDER\nworkspace: /root/.openclaw/workspace-PLACEHOLDER\nmodel: bailian/qwen3.5-plus\n",
    "config/old/deprecated_routing.json": json.dumps({
        "routes": [
            {"from": "feishu:old-hr", "to": "agent:hr-bot-v1"},
            {"from": "feishu:old-it", "to": "agent:it-bot-v1"}
        ]
    }, indent=2),
    "logs/2024/deployment_log_q4.txt": "2024-12-01 10:00 - Deployed finance-bot v2\n2024-12-15 14:30 - Deployed hr-bot v3\n",
    "logs/2025/deployment_log_q1.txt": "2025-01-10 09:00 - Deployed sales-bot v1\n2025-03-05 11:00 - Updated legal-bot config\n",
    "tests/unit/test_agent_naming.py": "import re\ndef test_agent_id_format():\n    assert re.match(r'^[a-z0-9-]+$', 'product-assistant')\n",
    "tests/integration/test_feishu_channel.py": "# Integration tests for feishu channel\n# Requires live credentials - skip in CI\nimport pytest\n@pytest.mark.skip(reason='requires live credentials')\ndef test_feishu_connection():\n    pass\n",
    "internal/bots/legacy/migration_notes.txt": "Legacy bots used a different agentId format (underscores).\nNew format requires lowercase-hyphen style.\nMigration completed 2024-09-01.\n",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# ── The main task input: a business request email ─────────────────────────────
task_request = """\
From: Zhang Wei <zhangwei@company.internal>
To: Platform Team <platform@company.internal>
Subject: New AI Bots Setup Request - Urgent

Hi team,

We need two new AI assistant bots deployed on our Feishu workspace ASAP.
Here are the details:

--- Bot 1 ---
新建 Bot: Aria-HR
职能：人力资源问答和招聘助理
模型：bailian/qwen3.5-plus
appId: cli_a1b2c3d4e5f6g7h8
appSecret: HRSecretKey2025XYZ99

--- Bot 2 ---
新建 Bot: CodeReview-Pro
职能：代码审查和技术文档生成
模型：bailian/qwen3-coder-plus
appId: cli_z9y8x7w6v5u4t3s2
appSecret: CodeSecretKey2025ABC88

Please get these set up and confirm when done.

Thanks,
Zhang Wei
Deputy Director, Digital Transformation
"""

with open(os.path.join(workspace, "bot_setup_request.txt"), "w") as f:
    f.write(task_request)

# ── Existing openclaw config (pre-existing state) ─────────────────────────────
openclaw_dir = "/root/.openclaw"
os.makedirs(openclaw_dir, exist_ok=True)

existing_config = {
    "version": "1.2.0",
    "gateway": {
        "port": 8080,
        "host": "0.0.0.0"
    },
    "agents": {
        "finance-bot": {
            "workspace": "/root/.openclaw/workspace-finance-bot",
            "model": "bailian/qwen3.5-plus",
            "createdAt": "2025-01-10T09:00:00Z"
        },
        "hr-legacy": {
            "workspace": "/root/.openclaw/workspace-hr-legacy",
            "model": "bailian/qwen3.5-plus",
            "createdAt": "2024-12-15T14:30:00Z"
        }
    },
    "channels": {
        "feishu": {
            "accounts": {
                "finance-bot": {
                    "appId": "cli_finance001",
                    "appSecret": "financeSecret001"
                }
            }
        }
    },
    "bindings": [
        "feishu:finance-bot -> finance-bot"
    ]
}

config_path = os.path.join(openclaw_dir, "openclaw.json")
with open(config_path, "w") as f:
    json.dump(existing_config, f, indent=2)

# ── Command log file (starts empty, mock openclaw appends to it) ──────────────
with open(os.path.join(openclaw_dir, "command_log.txt"), "w") as f:
    f.write("")

print("Workspace setup complete.")
print(f"Task file: {workspace}/bot_setup_request.txt")
print(f"Existing config: {openclaw_dir}/openclaw.json")