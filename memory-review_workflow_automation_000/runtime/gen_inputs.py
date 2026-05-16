import os
import random
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

BASE = Path("/workspace")

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "memory/daily",
    "memory/knowledge",
    "memory/projects",
    "memory/archive/2024",
    "data/exec-logs/memory-review",
    "data/exec-logs/other-skill",
    "data/raw",
    "data/cache",
    "scripts",
    "notes/scratch",
    "notes/meetings",
    "config",
]
for d in dirs:
    (BASE / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md ────────────────────────────────────────────────────────────────
skill_md = """\
---
name: memory-review
version: 1.1.0
description: 知识沉淀自动化技能。扫描近期日记，识别可沉淀知识，自动写入知识库。触发时机：cron 定时任务或手动调用。使用方法：加载 skill 后读取 references/spec.md 获取详细规范。
---

# Memory Review

扫描近期日记，生成知识沉淀提案，并自动执行沉淀。

## 核心流程

1. 读取 references/spec.md 获取详细规范
2. 读取 AGENTS.md/MEMORY.md 获取投递配置
3. 增量扫描近期日记（md5 比对）
4. 识别 5 类可沉淀知识
5. 自动写入知识库
6. 生成报告并投递

## 敏感信息

**投递配置（如飞书群ID）存储在 AGENTS.md 或 MEMORY.md 中**，skill 里使用占位符。

读取方式：
- 读取 `MEMORY.md`（如果存在）
- 读取 `AGENTS.md` 中的配置

## 输出

- 报告位置：`memory/daily/YYYY-MM-DD-memory-review.md`
- 知识库：`memory/knowledge/fw-*.md`
- 执行日志：`data/exec-logs/memory-review/YYYY-MM-DD.md`

## 触发时机

- cron 定时任务（建议每 2 天）
- 用户明确要求时
- 每次会话结束前（可选）

## 自动沉淀规则

| 优先级 | 条件 | 行为 |
|--------|------|------|
| 高 | 错误/教训类 | 自动写入 post-mortems.md |
| 中 | 技术知识类 | 自动写入 knowledge/fw-*.md |
| 低 | 配置/偏好类 | 写入 TOOLS.md 或 AGENTS.md |

## 沉淀文件命名规范

```
fw-{主题}.md
- fw = "from work" 工作产出
- 主题：用英文或中文拼音
```
"""
(BASE / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ── references/spec.md ──────────────────────────────────────────────────────
(BASE / "references").mkdir(parents=True, exist_ok=True)
spec_md = """\
# Memory Review — 详细规范 v1.1.0

## 增量扫描机制

- 状态文件路径：`data/cache/memory-review-state.json`
- 格式：`{ "scanned": { "<relative_path>": "<md5_hex>" } }`
- 对比逻辑：文件 md5 与状态文件中记录不同（或不存在）→ 视为新/变更，纳入本次扫描
- 扫描完成后**更新**状态文件，写入本次所有已扫描文件的 md5

## 日记扫描范围

- 目录：`memory/daily/`
- 文件格式：`YYYY-MM-DD.md`（不含 `*-memory-review.md` 后缀的文件）
- 扫描最近 **30 天**内的日记

## 5 类可沉淀知识识别规则

| 类型 | 关键词/标志 | 目标文件 |
|------|------------|---------|
| 错误/教训 | `# 错误`, `# 教训`, `# Bug`, `BUG`, `踩坑`, `排查` | `memory/post-mortems.md` |
| 技术知识 | `# 技术`, `# 原理`, `# 方案`, `# 实现`, `# 笔记` | `memory/knowledge/fw-{topic}.md` |
| 工具使用 | `# 工具`, `# 命令`, `# 用法`, `使用方式`, `CLI` | `memory/knowledge/fw-{topic}.md` |
| 配置/偏好 | `# 配置`, `# 偏好`, `# 设置`, `preference` | `TOOLS.md` |
| 项目经验 | `# 项目`, `# 复盘`, `# 总结` | `memory/knowledge/fw-{topic}.md` |

## 知识库文件写入规则

- 若 `fw-{topic}.md` 已存在，**追加**内容（不覆盖）
- 若不存在，新建文件，写入标准头部：
  ```
  # {topic}
  > 来源：memory-review 自动沉淀
  > 创建时间：YYYY-MM-DD
  ```
- `post-mortems.md` 同理：存在则追加，不存在则新建

## 报告格式

报告文件：`memory/daily/YYYY-MM-DD-memory-review.md`

```markdown
# Memory Review — YYYY-MM-DD

## 本次扫描

- 扫描文件数：N
- 新增/变更文件：M
- 沉淀条目数：K

## 沉淀详情

| 来源日记 | 知识类型 | 目标文件 |
|---------|---------|---------|
| ...     | ...     | ...     |

## 执行状态

- 状态：完成
- 时间：YYYY-MM-DD HH:MM
```

## 执行日志格式

日志文件：`data/exec-logs/memory-review/YYYY-MM-DD.md`

```markdown
# Execution Log — YYYY-MM-DD

## Steps

1. 读取状态文件
2. 扫描日记目录
3. MD5 对比，识别变更文件
4. 知识分类与写入
5. 更新状态文件
6. 生成报告

## Result

- scanned: N files
- new/changed: M files
- deposited: K items
```
"""
(BASE / "references" / "spec.md").write_text(spec_md, encoding="utf-8")

# ── AGENTS.md ───────────────────────────────────────────────────────────────
agents_md = """\
# Agents Configuration

## memory-review

- feishu_group_id: PLACEHOLDER_GROUP_ID
- report_webhook: PLACEHOLDER_WEBHOOK
- auto_deposit: true
- scan_days: 30
"""
(BASE / "AGENTS.md").write_text(agents_md, encoding="utf-8")

# ── TOOLS.md (exists but nearly empty) ──────────────────────────────────────
(BASE / "TOOLS.md").write_text("# Tools\n\n(暂无条目)\n", encoding="utf-8")

# ── Diary entries — the real inputs ─────────────────────────────────────────
today = datetime.now().date()

diaries = {}

# Diary 1: contains error/lesson content  (should go to post-mortems.md)
d1_date = today - timedelta(days=1)
diaries[d1_date] = f"""\
# {d1_date} 日记

## 日常工作

今天主要调试了数据管道问题，修了一个困扰很久的 bug。

## 踩坑记录

### 排查：Celery worker 内存泄漏

# 错误

在使用 Celery 4.x 时，若任务闭包捕获了大型 DataFrame 对象，worker 内存会持续增长，
最终 OOM 被 kill。

**根因**：Celery 的 task result backend 默认保留所有结果引用，导致 GC 无法回收。

**解决方案**：
- 设置 `task_ignore_result = True`
- 或在任务完成后显式调用 `AsyncResult.forget()`

# 教训

不要在 Celery task 函数体外部定义大型数据结构并在 task 中引用，
否则每个 worker 进程都会持有一份副本。
"""

# Diary 2: contains technical knowledge  (should go to fw-*.md)
d2_date = today - timedelta(days=2)
diaries[d2_date] = f"""\
# {d2_date} 日记

## 技术研究

今天深入研究了 Python asyncio event loop 的调度机制。

# 技术

## asyncio 任务调度原理

asyncio 使用单线程事件循环，通过 `select`/`epoll` 多路复用实现并发。
关键点：
- `await` 表达式会挂起当前协程，将控制权交还事件循环
- IO 密集型任务受益于 asyncio，CPU 密集型应用 `run_in_executor`
- `asyncio.gather()` 并发调度多协程，但仍在同一线程

# 方案

对于需要同时处理数千 WebSocket 连接的场景，推荐使用 `asyncio` + `uvloop`，
uvloop 基于 libuv，性能比标准 asyncio 快 2~4 倍。
"""

# Diary 3: contains tool/command content (should go to fw-*.md)
d3_date = today - timedelta(days=3)
diaries[d3_date] = f"""\
# {d3_date} 日记

## 工具学习

今天整理了 ripgrep 的高效使用方式。

# 工具

## ripgrep 常用命令速查

使用方式：

```bash
# 递归搜索，忽略 .gitignore
rg "pattern" /path/to/dir

# 只搜索特定文件类型
rg -t py "import asyncio"

# 显示行号和文件名
rg -n --with-filename "TODO"

# 搜索并替换（配合 sed）
rg -l "old_func" | xargs sed -i 's/old_func/new_func/g'
```

CLI 工具，速度比 grep 快 10x，支持 Unicode，自动跳过二进制文件。
"""

# Diary 4: contains config/preference content (should go to TOOLS.md)
d4_date = today - timedelta(days=5)
diaries[d4_date] = f"""\
# {d4_date} 日记

## 环境配置

今天统一了本地开发环境配置。

# 配置

## Python 开发偏好设置

preference: 使用 `pyenv` 管理 Python 版本，不用系统 Python。
- Python 3.11 作为默认版本
- 使用 `uv` 替代 pip，速度快 10x

# 偏好

编辑器：Neovim + LazyVim 配置
终端：Wezterm + fish shell
代码风格：black + ruff，行宽 88
"""

# Diary 5: contains project retrospective (should go to fw-*.md)
d5_date = today - timedelta(days=7)
diaries[d5_date] = f"""\
# {d5_date} 日记

## 项目总结

# 项目

## 数据同步服务 v2 复盘

# 复盘

**背景**：为客户构建实时数据同步服务，从 MySQL binlog 同步到 Elasticsearch。

**关键决策**：
- 使用 Debezium + Kafka 而非直接轮询，降低源库压力
- ES bulk insert 批量大小设为 500，在吞吐量和延迟间取得平衡

**经验**：
- Debezium connector 配置 `snapshot.mode=initial` 首次全量同步很慢，
  生产环境应提前评估时间窗口
- Kafka consumer group 的 `auto.offset.reset=earliest` 配置需谨慎，
  重启后可能重复消费

# 总结

整体项目成功，但 schema 变更处理较麻烦，建议后续引入 schema registry。
"""

# Write diary files
for date, content in diaries.items():
    fpath = BASE / "memory" / "daily" / f"{date}.md"
    fpath.write_text(content, encoding="utf-8")

# ── Stale state file: has MD5 for d4 and d5 (already "scanned"), 
#    but NOT for d1, d2, d3 → agent should only process d1, d2, d3 as new
# ─────────────────────────────────────────────────────────────────────────────
def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()

state = {
    "scanned": {
        f"memory/daily/{d4_date}.md": md5_of(BASE / "memory" / "daily" / f"{d4_date}.md"),
        f"memory/daily/{d5_date}.md": md5_of(BASE / "memory" / "daily" / f"{d5_date}.md"),
    }
}
(BASE / "data" / "cache" / "memory-review-state.json").write_text(
    json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
)

# ── Old knowledge file that should be APPENDED to (not overwritten) ──────────
existing_fw = BASE / "memory" / "knowledge" / "fw-asyncio.md"
existing_fw.write_text(
    "# asyncio\n> 来源：memory-review 自动沉淀\n> 创建时间：2024-11-01\n\n"
    "## 旧内容：asyncio 基础\n\nCoroutine 基础略。\n",
    encoding="utf-8",
)

# ── Distractor files ─────────────────────────────────────────────────────────
(BASE / "memory" / "archive" / "2024" / "q3-summary.md").write_text(
    "# Q3 2024 年度总结\n\n旧内容，不在扫描范围内。\n", encoding="utf-8"
)
(BASE / "memory" / "projects" / "project-alpha.md").write_text(
    "# Project Alpha\n\n项目文档，不是日记。\n", encoding="utf-8"
)
(BASE / "notes" / "scratch" / "random-idea.md").write_text(
    "随手记：买咖啡豆\n", encoding="utf-8"
)
(BASE / "notes" / "meetings" / "2025-01-15-standup.md").write_text(
    "# Standup 2025-01-15\n\n- Alice: 正在做 API 重构\n- Bob: 修复了登录 bug\n",
    encoding="utf-8",
)
(BASE / "data" / "raw" / "metrics-2025.csv").write_text(
    "date,value\n2025-01-01,42\n2025-01-02,55\n", encoding="utf-8"
)
(BASE / "data" / "exec-logs" / "other-skill" / "2025-01-10.md").write_text(
    "# Other Skill Log\n\n无关日志。\n", encoding="utf-8"
)
(BASE / "scripts" / "deploy.sh").write_text(
    "#!/bin/bash\necho 'deploy'\n", encoding="utf-8"
)
(BASE / "config" / "settings.yaml").write_text(
    "env: production\ndebug: false\n", encoding="utf-8"
)
(BASE / "memory" / "daily" / "2024-08-15.md").write_text(
    "# 2024-08-15\n\n旧日记，超出 30 天扫描范围。\n", encoding="utf-8"
)
(BASE / "memory" / "knowledge" / "fw-docker.md").write_text(
    "# docker\n> 来源：manual\n\nDocker 常用命令。\n", encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Today: {today}")
print(f"New diaries (not in state): {d1_date}, {d2_date}, {d3_date}")
print(f"Already-scanned diaries (in state): {d4_date}, {d5_date}")