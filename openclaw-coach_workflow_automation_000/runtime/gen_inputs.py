import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create the SKILL.md in the workspace
skill_md = """---
name: openclaw-coach
description: OpenClaw 私人教练 - 每日文档同步+技巧教学。用于 (1) 每天自动从官网同步最新文档到 Obsidian 知识库 (2) 每天早上 7:21 发送 OpenClaw 使用技巧 (3) 每天晚上 21:05 让用户选择想了解的技巧主题 (4) 检测 OpenClaw 版本更新并提醒
---

# OpenClaw 教练

你的私人 OpenClaw 教练，负责文档同步和每日技巧教学。

## 定时任务

| 时间 | 任务 | 脚本 |
|------|------|------|
| 03:21 | 文档同步 | `scripts/sync-docs.sh` |
| 21:05 | 技巧选择 | `scripts/pick-daily-tip.sh` |
| 07:21 | 发送技巧 | `scripts/send-daily-tip.sh` |

## 知识库结构

```
Obsidian/Docs/OpenClaw/
├── docs/                    # 官方文档
│   ├── gateway.md
│   ├── channels.md
│   └── ...
├── tips/                    # 技巧文章
│   ├── gateway-使用指南.md
│   ├── message-发送消息.md
│   └── ...
├── daily-tips.json         # 每日技巧选择
├── tips-log.md             # 发送日志
└── latest-version.txt      # 当前版本
```

## 技巧文章模板

```markdown
# 技巧标题

## 简介
简短介绍这个技巧是什么

## 使用场景
- 场景1
- 场景2

## 详细步骤
1. 步骤一
2. 步骤二

## 示例
\\`\\`\\`bash
openclaw gateway start
\\`\\`\\`

## 注意事项
- 注意1
```

## 用户交互流程

1. **晚上 21:05**: 发送3个技巧选项让用户选择
2. **用户回复数字**: 记录选择
3. **早上 7:21**: 发送选中技巧的详细内容 + 版本更新（如有）

## 事件处理

当收到以下系统事件时，自动执行对应操作：

| 事件 | 动作 |
|------|------|
| `sync` | 执行 `scripts/sync-docs.sh` |
| `pick-tip` | 执行 `scripts/pick-daily-tip.sh` |
| `send-tip` | 执行 `scripts/send-daily-tip.sh` |

## 手动命令

- `/sync` - 立即同步文档
- `/tip` - 查看今日技巧
- `/tips list` - 查看所有可用技巧
"""

(workspace / "SKILL.md").write_text(skill_md, encoding="utf-8")

# Create scripts directory with stub scripts
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

(scripts_dir / "sync-docs.sh").write_text("#!/bin/bash\necho 'Syncing docs...'\n")
(scripts_dir / "pick-daily-tip.sh").write_text("#!/bin/bash\necho 'Picking daily tip...'\n")
(scripts_dir / "send-daily-tip.sh").write_text("#!/bin/bash\necho 'Sending daily tip...'\n")

# Create a partial, broken Obsidian structure as the "messy initial state"
obsidian_base = workspace / "Obsidian" / "Docs" / "OpenClaw"
obsidian_base.mkdir(parents=True, exist_ok=True)

# Create a docs folder with some existing (distractor) docs
docs_dir = obsidian_base / "docs"
docs_dir.mkdir(exist_ok=True)

(docs_dir / "gateway.md").write_text("""# Gateway Documentation
OpenClaw gateway is the main entry point for all connections.
Use `openclaw gateway start` to initialize.
""")

(docs_dir / "channels.md").write_text("""# Channels Documentation
Channels allow multiplexed communication streams.
""")

(docs_dir / "auth.md").write_text("""# Authentication
Token-based auth is used for all requests.
""")

# Create a broken/empty tips directory (agent must populate it)
tips_dir = obsidian_base / "tips"
tips_dir.mkdir(exist_ok=True)

# Leave a malformed stub tip that agent should NOT use as reference (it's wrong)
(tips_dir / "BROKEN-stub.md").write_text("""# Wrong format tip

This file has the wrong structure and should not be used as a template.
Missing all required sections.
Just some random notes here.
""")

# Create an empty (missing data) daily-tips.json - it's malformed
(obsidian_base / "daily-tips.json").write_text("{}")

# Create an empty tips-log
(obsidian_base / "tips-log.md").write_text("")

# Missing latest-version.txt intentionally - agent must create it

# Distractor files to test contextual awareness
distractor_dir = workspace / "misc"
distractor_dir.mkdir(exist_ok=True)

(distractor_dir / "old-config.yaml").write_text("""version: 0.1
deprecated: true
notes: this is an old config, ignore it
""")

(distractor_dir / "scratch.txt").write_text("random notes\ntodo: figure out cron\n")

notes_dir = workspace / "notes"
notes_dir.mkdir(exist_ok=True)

(notes_dir / "meeting-2024-01-15.md").write_text("""# Meeting Notes
Discussed OpenClaw integration.
Need to set up tips system.
""")

(notes_dir / "ideas.md").write_text("""# Ideas
- automate daily tips
- track version updates
""")

(notes_dir / "todo.txt").write_text("setup openclaw coach\nconfigure obsidian\n")

archive_dir = workspace / "archive" / "2023"
archive_dir.mkdir(parents=True, exist_ok=True)

(archive_dir / "old-tips-draft.md").write_text("""Old draft format - wrong sections
Introduction here
Steps here
No proper template used
""")

(archive_dir / "version-history.txt").write_text("v1.0.0\nv1.1.0\nv1.2.0\n")

config_dir = workspace / "config"
config_dir.mkdir(exist_ok=True)

(config_dir / "cron-ideas.txt").write_text("""# Cron schedule ideas (NOT final)
03:21 sync
07:21 send tip
21:05 pick tip
""")

(config_dir / "paths-draft.txt").write_text("Obsidian base path TBD\n")

# Create a raw "topics" file that the agent should use to create tip articles
# These are unstructured raw notes - agent must turn them into proper tip articles
(workspace / "raw-tip-topics.txt").write_text("""Topic 1: gateway-使用指南
- gateway is the core component
- start with: openclaw gateway start
- can specify port with --port flag
- supports TLS via --tls flag
- tip: always check status with openclaw gateway status

Topic 2: message-发送消息  
- send messages using the message command
- basic usage: openclaw message send "hello"
- can target specific channel with --channel flag
- supports markdown formatting
- tip: use --async flag for non-blocking sends

Topic 3: channel-管理频道
- channels organize message streams
- create: openclaw channel create myChannel
- list all: openclaw channel list
- delete: openclaw channel delete myChannel
- tip: use descriptive channel names
""")

print("Workspace generated successfully.")
print(f"Structure created at: {workspace}")