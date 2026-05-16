import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create the SKILL.md so the agent can read it
skill_md = workspace / "SKILL.md"
skill_md.write_text(r"""# work-windows — 多窗口工作台 🪟

> Manage multiple independent work windows with context isolation

一个帮助你管理多个独立工作窗口的技能，每个窗口有独立的上下文，切换时可以自动保存和恢复工作进度。

---

## 📋 Changelog

### v1.1 (2026-03-25)
- **切换时自动保存对话历史** — 读取当前 session 的 transcript.jsonl 保存到窗口目录
- **切回时加载历史** — 切换到窗口时自动显示之前保存的对话记录
- **真正上下文隔离** — 每个窗口有独立的 transcript，不会污染其他窗口

### v1.0 (2026-03-14) - 初始版本
- 多窗口管理基础功能
- 开窗口、切窗口、列窗口、完成窗口

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 开窗口 | 创建新窗口，分配独立 session |
| 切窗口 | 自动保存当前对话 + 加载历史 |
| 列窗口 | 列出所有窗口及状态 |
| 查窗口 | 按时间段查询历史窗口 |
| 完成窗口 | 标记窗口完成 |
| 保存摘要 | 保存工作进度 |

---

## 🗂️ 窗口目录结构

```
memory/tasks/
├── tasks.json              # 窗口索引
├── current.json            # 当前窗口
├── {ID}{名称}/
│   ├── meta.json           # 窗口元信息
│   ├── summary.md          # 工作摘要
│   └── output/
│       └── transcript.jsonl # 完整对话历史
```

---

## 📖 命令指南

### 开窗口 / Create Window

```
你说：开窗口 调研报告

回复：✅ 已创建窗口 0314-4（调研报告）
```

### 列窗口 / List Windows

```
你说：列窗口

回复：📋 窗口列表：...
```

### 切窗口 / Switch Window

```
你说：切到 0315-3

回复：
🔄 已切换到窗口 0315-3（知识库设计）

📜 历史对话：
**user**: ...
**assistant**: ...
```

### 保存摘要

```
你说：保存摘要 完成了需求分析，待做UI设计

回复：✅ 已更新工作摘要
```

---

有问题随时问！😊
""", encoding="utf-8")

# Create distractor directory structure (10+ distractor files)
distractors = [
    "notes/client_alpha/meeting_2024_01.txt",
    "notes/client_alpha/requirements_v2.txt",
    "notes/client_beta/proposal_draft.txt",
    "notes/client_beta/budget_estimate.csv",
    "archive/old_tasks/task_001.json",
    "archive/old_tasks/task_002.json",
    "archive/old_tasks/task_003.json",
    "archive/reports/quarterly_summary_q1.md",
    "archive/reports/quarterly_summary_q2.md",
    "config/app_settings.json",
    "config/db_config.yaml",
    "logs/error_2024_01_15.log",
    "logs/access_2024_01_15.log",
    "temp/scratch_notes.txt",
    "temp/ideas_dump.md",
]

distractor_contents = {
    "notes/client_alpha/meeting_2024_01.txt": "Meeting notes: Discussed project timeline and deliverables. Action items: None.",
    "notes/client_alpha/requirements_v2.txt": "REQ-001: System must handle 1000 concurrent users.\nREQ-002: Response time < 200ms.",
    "notes/client_beta/proposal_draft.txt": "Draft proposal for Client Beta - Phase 1 implementation.",
    "notes/client_beta/budget_estimate.csv": "Phase,Cost\nDesign,50000\nDev,120000\nTesting,30000",
    "archive/old_tasks/task_001.json": json.dumps({"id": "task_001", "status": "closed", "name": "Legacy migration"}),
    "archive/old_tasks/task_002.json": json.dumps({"id": "task_002", "status": "closed", "name": "API redesign"}),
    "archive/old_tasks/task_003.json": json.dumps({"id": "task_003", "status": "closed", "name": "Database schema update"}),
    "archive/reports/quarterly_summary_q1.md": "# Q1 Summary\n\n- Completed 3 projects\n- Revenue: $200k",
    "archive/reports/quarterly_summary_q2.md": "# Q2 Summary\n\n- Completed 5 projects\n- Revenue: $350k",
    "config/app_settings.json": json.dumps({"env": "production", "debug": False, "max_workers": 4}),
    "config/db_config.yaml": "host: localhost\nport: 5432\ndbname: consulting_db",
    "logs/error_2024_01_15.log": "[ERROR] 2024-01-15 10:23:45 - Connection timeout\n[ERROR] 2024-01-15 11:05:12 - Null pointer exception",
    "logs/access_2024_01_15.log": "[INFO] 2024-01-15 09:00:00 - User admin logged in\n[INFO] 2024-01-15 09:05:00 - Report generated",
    "temp/scratch_notes.txt": "TODO: Follow up with client on API specs\nTODO: Review security audit results",
    "temp/ideas_dump.md": "# Random Ideas\n\n- Use microservices architecture\n- Consider GraphQL for flexible queries",
}

for filepath, content in distractor_contents.items():
    full_path = workspace / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# Create a deliberately malformed/incomplete memory/tasks structure
# to simulate a real messy environment (tasks dir exists but is incomplete)
tasks_dir = workspace / "memory" / "tasks"
tasks_dir.mkdir(parents=True, exist_ok=True)

# Write a CORRUPTED/INCOMPLETE tasks.json (missing required fields, wrong structure)
# This is the "messy" starting state — agent must recognize and fix/replace it
broken_tasks_json = {
    "version": "0.9",
    "items": []  # Wrong key — should be "windows" or some proper structure per SKILL.md
}
(tasks_dir / "tasks.json").write_text(json.dumps(broken_tasks_json, indent=2), encoding="utf-8")

# No current.json exists yet — agent must create it
# No window directories exist yet — agent must create them

print("Workspace initialized with distractor files and incomplete task structure.")
print("Directory tree:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")