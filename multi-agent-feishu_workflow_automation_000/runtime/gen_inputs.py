#!/usr/bin/env python3
"""
Generate the sandbox workspace for the multi-agent-feishu task.
Creates a realistic, messy environment that forces the agent to
read SKILL.md and apply proprietary OpenClaw configuration logic.
"""

import json
import os
import random
import stat
from pathlib import Path

random.seed(42)

# ─────────────────────────── Workspace root ────────────────────────────
workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ─────────────────────────── SKILL.md ──────────────────────────────────
skill_md = """\
---
name: multi-agent-feishu
description: |
  在 OpenClaw Gateway 中创建多个 Agent 并绑定多个飞书账号。
  适用于：(1) 需要多个独立 AI 助手 (2) 不同用户使用不同 Agent (3) 需要隔离的记忆/身份场景。
---

# Multi-Agent Feishu Setup

在同一个 OpenClaw Gateway 下创建多个 Agent，每个绑定不同飞书机器人。

## 快速开始

### 1. 创建 Agent

```bash
openclaw agents add <agent_id> \\
  --workspace ~/.openclaw/workspace<N> \\
  --bind feishu:<account_id> \\
  --non-interactive
```

### 2. 添加飞书账号

编辑 `~/.openclaw/openclaw.json`，在 `channels.feishu.accounts` 中添加：

```json
"<account_id>": {
  "appId": "cli_xxx",
  "appSecret": "xxx"
}
```

### 3. 重启 Gateway

```bash
openclaw gateway restart
```

### 4. 配对飞书

```bash
openclaw pairing approve feishu <配对码>
```

## 验证配置

```bash
openclaw agents list --bindings
```

## 详细文档

- [配置字段说明](references/config-fields.md) - agents.list、bindings、channels 字段详解
- [飞书机器人创建指南](references/feishu-app.md) - 如何在飞书开放平台创建机器人
- [多 Agent 架构图](references/architecture.md) - 架构说明和流程图
- [常见问题](references/faq.md) - 配对失败、收不到消息等问题排查
- [备份与恢复](references/backup.md) - 配置备份和恢复方法
"""
(workspace / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ─────────────────────────── ~/.openclaw/ skeleton ─────────────────────
openclaw_dir = Path.home() / ".openclaw"
openclaw_dir.mkdir(exist_ok=True)

# Intentionally BROKEN / incomplete openclaw.json — missing the accounts
# sub-structure that the agent must add.
broken_config = {
    "gateway": {
        "host": "127.0.0.1",
        "port": 8080,
        "logLevel": "info"
    },
    "channels": {
        "feishu": {
            # 'accounts' key is MISSING — agent must add it with proper structure
        }
    },
    "agents": []
}
(openclaw_dir / "openclaw.json").write_text(
    json.dumps(broken_config, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# Pre-create workspace dirs for potential confusion (wrong numbering scheme)
for i in [0, 9, 99]:
    (openclaw_dir / f"workspace{i}").mkdir(exist_ok=True)

# ─────────────────────────── Distractor files ──────────────────────────
# 1. Fake old config backup
old_config = {
    "gateway": {"host": "localhost", "port": 9999},
    "channels": {"slack": {"accounts": {"old_slack": {"token": "xoxb-fake"}}}},
    "agents": [{"id": "legacy-bot", "workspace": "/old/path", "bind": "slack:old_slack"}]
}
(openclaw_dir / "openclaw.json.bak").write_text(
    json.dumps(old_config, indent=2), encoding="utf-8"
)

# 2. Distractor env file
(openclaw_dir / ".env.example").write_text(
    "OPENCLAW_PORT=8080\nOPENCLAW_HOST=0.0.0.0\nFEISHU_WEBHOOK=https://example.com\n",
    encoding="utf-8"
)

# 3. Fake migration script (distractor)
(workspace / "migrate_agents.sh").write_text(
    "#!/bin/bash\n# Legacy migration — DO NOT USE\necho 'migrate old config'\n",
    encoding="utf-8"
)

# 4. Misleading notes dir
notes_dir = workspace / "notes"
notes_dir.mkdir(exist_ok=True)
(notes_dir / "setup_notes.txt").write_text(
    "Old approach: manually edit agents.yaml\nNew approach: use CLI tool\n"
    "Remember: restart after config changes!\n",
    encoding="utf-8"
)
(notes_dir / "feishu_creds.txt").write_text(
    "Sales bot:\n  App ID: cli_sales_app_001\n  App Secret: s3cr3t_sales_2024\n\n"
    "Support bot:\n  App ID: cli_support_app_002\n  App Secret: s3cr3t_support_2024\n",
    encoding="utf-8"
)

# 5. Fake references directory (distractor — no useful content)
refs_dir = workspace / "references"
refs_dir.mkdir(exist_ok=True)
for fname in ["config-fields.md", "feishu-app.md", "architecture.md", "faq.md", "backup.md"]:
    (refs_dir / fname).write_text(
        f"# {fname}\n\n(Content not yet migrated to this environment.)\n",
        encoding="utf-8"
    )

# 6. Fake python venv leftovers
venv_dir = workspace / ".venv" / "lib"
venv_dir.mkdir(parents=True, exist_ok=True)
(venv_dir / "site-packages.txt").write_text("openclaw==0.9.1\n", encoding="utf-8")

# 7. Misleading docker-compose
(workspace / "docker-compose.yml").write_text(
    "version: '3'\nservices:\n  gateway:\n    image: openclaw/gateway:latest\n"
    "    ports:\n      - '8080:8080'\n",
    encoding="utf-8"
)

# 8. Fake agent config in wrong format (YAML, not JSON)
(workspace / "agents_wrong_format.yaml").write_text(
    "agents:\n  - id: sales-agent\n    workspace: /wrong/path\n    feishu_app: cli_sales_wrong\n",
    encoding="utf-8"
)

# 9. Deployment checklist (distractor)
(workspace / "deployment_checklist.md").write_text(
    "# Deployment Checklist\n\n"
    "- [ ] Create Feishu bots in developer portal\n"
    "- [ ] Add credentials to config\n"
    "- [ ] Register agents\n"
    "- [ ] Restart gateway\n"
    "- [ ] Verify bindings\n",
    encoding="utf-8"
)

# 10. Leftover log file
logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)
(logs_dir / "gateway.log").write_text(
    "[2024-01-15 09:00:00] Gateway started on :8080\n"
    "[2024-01-15 09:00:01] No agents registered\n"
    "[2024-01-15 09:01:00] WARNING: channels.feishu.accounts is empty\n",
    encoding="utf-8"
)

# ─────────────────────────── Task specification ────────────────────────
# Write a task brief — business framing, NOT a tutorial
task_brief = """\
# Task Brief

Our company is deploying two independent AI assistants via the OpenClaw Gateway:

1. **Sales Department Bot**
   - Agent ID  : sales-agent
   - Account ID: feishu-sales
   - Feishu App ID    : cli_sales_app_001
   - Feishu App Secret: s3cr3t_sales_2024
   - Workspace number : 1

2. **Support Department Bot**
   - Agent ID  : support-agent
   - Account ID: feishu-support
   - Feishu App ID    : cli_support_app_002
   - Feishu App Secret: s3cr3t_support_2024
   - Workspace number : 2

Both agents must be independently configured, registered, and the gateway
must be restarted after setup so the new configuration takes effect.

See SKILL.md for the correct setup procedure.
"""
(workspace / "TASK_BRIEF.md").write_text(task_brief, encoding="utf-8")

print("Workspace generated successfully.")
print(f"  OpenClaw config: {openclaw_dir / 'openclaw.json'}")
print(f"  Task brief     : {workspace / 'TASK_BRIEF.md'}")