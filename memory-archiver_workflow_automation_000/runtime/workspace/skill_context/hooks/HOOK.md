---
name: auto-memory-search
description: "Auto-search memory when detecting questions, bugs, specs, configs, or tech keywords in user messages"
metadata:
  {
    "openclaw":
      {
        "emoji": "🔍",
        "events": ["message:received"],
        "install": [{ "id": "local", "kind": "local", "label": "Local workspace hook" }],
      },
  }
---

# Auto Memory Search Hook

Automatically searches memory files when user messages contain questions, bug reports, spec references, config inquiries, or technical keywords.

## What It Does

1. **Detects message type** - Identifies 7 categories: 疑问/修复/规范/特征/配置/命令/技术
2. **Extracts keywords** - Pulls key terms from the message
3. **Searches memory** - Runs `auto-memory-search.sh` against memory files
4. **Injects context** - Appends relevant memory snippets to the message context

## Supported Message Types

| Type | Trigger Keywords |
|------|-----------------|
| 疑问 | 怎么, 如何, 为什么, what, how, why |
| 修复 | bug, 错误, 修复, fix, error |
| 规范 | 规范, 规则, 标准, spec, rule |
| 特征 | 特征, 特点, feature |
| 配置 | 配置, 设置, 安装, config, setup |
| 命令 | 命令, 脚本, command, script |
| 技术 | css, html, php, javascript, tailwind, vite |

## Requirements

- `skills/memory-archiver/scripts/auto-memory-search.sh` must exist

## Disabling

```bash
openclaw hooks disable auto-memory-search
```
