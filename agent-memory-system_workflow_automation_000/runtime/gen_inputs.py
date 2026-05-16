#!/usr/bin/env python3
"""
Generate a realistic, messy workspace simulating an AI assistant's memory system
after months of operation. The agent must clean up old logs, create a new lesson,
run GC to archive cold data, and extract a skill.
"""

import os
import stat
from pathlib import Path
from datetime import datetime, timedelta

# Fixed seed for determinism
import random
random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory Structure ──────────────────────────────────────────────────────
dirs = [
    "memory/lessons",
    "memory/decisions",
    "memory/people",
    "memory/reflections",
    "memory/.archive",
    "skills",
    "logs",
    ".openclaw/workspace/skills/agent-memory-system/scripts",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Helper ───────────────────────────────────────────────────────────────────
def write(path, content):
    p = WORKSPACE / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p

def set_mtime(path, days_ago):
    """Set file modification time to simulate age."""
    target = datetime.now() - timedelta(days=days_ago)
    ts = target.timestamp()
    os.utime(path, (ts, ts))

# ── TODAY / REFERENCE DATES ──────────────────────────────────────────────────
today = datetime.now()

# ── COLD daily logs (45–60 days old) ─────────────────────────────────────────
cold_dates = [today - timedelta(days=d) for d in [45, 50, 53, 58, 62]]
for dt in cold_dates:
    fname = f"memory/{dt.strftime('%Y-%m-%d')}.md"
    content = f"""# {dt.strftime('%Y-%m-%d')}

## 完成
- [DB 监控脚本] - 已部署
- [告警规则更新] - 已配置

## 问题
- [磁盘空间不足] - 临时清理

## 明天
- [审查备份策略]
"""
    p = write(fname, content)
    set_mtime(p, (today - dt).days)

# ── WARM daily logs (10–20 days old) ─────────────────────────────────────────
warm_dates = [today - timedelta(days=d) for d in [10, 15, 18]]
for dt in warm_dates:
    fname = f"memory/{dt.strftime('%Y-%m-%d')}.md"
    content = f"""# {dt.strftime('%Y-%m-%d')}

## 完成
- [代码审查] - 通过
- [单元测试] - 全绿

## 问题
- 无

## 明天
- [性能优化调研]
"""
    p = write(fname, content)
    set_mtime(p, (today - dt).days)

# ── HOT daily log (today) ────────────────────────────────────────────────────
today_log = f"memory/{today.strftime('%Y-%m-%d')}.md"
write(today_log, f"""# {today.strftime('%Y-%m-%d')}

## 完成
- [生产数据库回滚演练] - 完成，发现重大教训

## 问题
- [回滚脚本缺少幂等性检查] - 导致数据短暂不一致

## 明天
- [编写数据库回滚规范]
- [创建生产DB回滚教训记录]
""")

# ── Existing LESSON with MALFORMED frontmatter (distractor) ──────────────────
write("memory/lessons/api-timeout-handling.md", """---
title: "API 超时处理"
date: 2024-11-10
category: lessons
lesson_id: LRN-20241110-001
priority: 🟡
status: active
---

# API 超时处理

## 背景
生产环境下游服务偶发超时导致级联失败。

## 问题
未设置合理的 timeout 和 retry 策略。

## 原因
默认 HTTP client 无超时限制。

## 解决方案
统一使用带指数退避的 retry 中间件。

## 预防
- 所有外部调用必须设置 timeout
- 接入熔断器
""")

# ── Lessons README ────────────────────────────────────────────────────────────
write("memory/lessons/README.md", """# 教训索引

| ID | 主题 | 类别 | 状态 |
|----|------|------|------|
| LRN-20241110-001 | API 超时处理 | reliability | active |
""")

# ── Decisions ────────────────────────────────────────────────────────────────
dec_date = today - timedelta(days=20)
write(f"memory/decisions/{dec_date.strftime('%Y-%m-%d')}-adopt-postgres.md", f"""---
date: {dec_date.strftime('%Y-%m-%d')}
title: "采用 PostgreSQL 作为主数据库"
status: approved
---

# 采用 PostgreSQL 作为主数据库

选择 PostgreSQL 替换 MySQL，主要因素：JSONB 支持、扩展生态。
""")

write("memory/decisions/README.md", """# 决策索引

| 日期 | 决策 | 状态 |
|------|------|------|
| 2024-12-XX | 采用 PostgreSQL | approved |
""")

# ── People ───────────────────────────────────────────────────────────────────
write("memory/people/alice.md", """# Alice Chen

## 角色
SRE Lead

## 关键信息
- 负责数据库基础设施
- 联系方式: alice@company.internal

## 互动记录
- 2024-11: 协作完成灾备演练
""")

# ── Reflections (distractor) ─────────────────────────────────────────────────
ref_date = today - timedelta(days=3)
write(f"memory/reflections/{ref_date.strftime('%Y-%m-%d')}-weekly.md", f"""# 周反思 {ref_date.strftime('%Y-%m-%d')}

## 健康度
- MEMORY.md: 2.1KB ✅
- 热数据: 3个
- 教训数量: 1

## 待处理
- 生产DB回滚事件需要记录教训
""")

# ── memory/INDEX.md ───────────────────────────────────────────────────────────
write("memory/INDEX.md", """# Memory Index

## 快速导航

- [MEMORY.md](../MEMORY.md) - 核心长期记忆
- [lessons/](lessons/) - 经验教训
- [decisions/](decisions/) - 重大决策
- [people/](people/) - 人物档案
- [reflections/](reflections/) - 反思记录
- [.archive/](.archive/) - 归档数据

## 最近更新
- 今日: 生产DB回滚演练
""")

# ── MEMORY.md (core, 2.5KB, under 5KB limit) ─────────────────────────────────
write("MEMORY.md", """# MEMORY.md - 长期记忆

> 核心知识和决策的精华

## 核心决策

| 决策 | 状态 | 优先级 | 最后更新 |
|------|------|--------|----------|
| 采用 PostgreSQL | approved | 高 | 2024-12 |
| 微服务拆分计划 | pending | 中 | 2024-11 |

## 最佳实践

- 所有外部 API 调用必须设置 timeout
- 数据库迁移必须有回滚脚本
- 部署前必须在 staging 环境验证

## 经验教训索引

| ID | 主题 | 类别 | 状态 |
|----|------|------|------|
| LRN-20241110-001 | API 超时处理 | reliability | active |

## 系统健康度

- 最后 GC: 从未运行
- 热数据: 1个
- 教训总数: 1
""")

# ── The actual shell SCRIPTS (already "installed") ───────────────────────────
scripts_dir = WORKSPACE / ".openclaw/workspace/skills/agent-memory-system/scripts"

# memory-gc.sh
(scripts_dir / "memory-gc.sh").write_text(r"""#!/bin/bash
# memory-gc.sh - 自动归档冷数据（>30天）
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"
MEMORY_DIR="$WORKSPACE/memory"
ARCHIVE_DIR="$MEMORY_DIR/.archive"
LOG_FILE="$WORKSPACE/logs/memory-gc.log"
REPORT_FILE="$WORKSPACE/logs/gc-report.md"

mkdir -p "$ARCHIVE_DIR" "$WORKSPACE/logs"

echo "=== Memory GC Started: $(date) ===" | tee -a "$LOG_FILE"

HOT=0; WARM=0; COLD=0; ARCHIVED=0

NOW=$(date +%s)

while IFS= read -r -d '' file; do
    filename=$(basename "$file")
    # Only process YYYY-MM-DD.md daily logs
    if [[ ! "$filename" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$ ]]; then
        continue
    fi
    
    # Get file modification time
    FMTIME=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)
    AGE_DAYS=$(( (NOW - FMTIME) / 86400 ))
    
    if [ "$AGE_DAYS" -lt 7 ]; then
        HOT=$((HOT+1))
    elif [ "$AGE_DAYS" -le 30 ]; then
        WARM=$((WARM+1))
    else
        COLD=$((COLD+1))
        # Extract YYYY-MM from filename
        YEAR_MONTH="${filename:0:7}"
        TARGET_DIR="$ARCHIVE_DIR/$YEAR_MONTH"
        mkdir -p "$TARGET_DIR"
        mv "$file" "$TARGET_DIR/"
        echo "  [ARCHIVED] $filename -> .archive/$YEAR_MONTH/" | tee -a "$LOG_FILE"
        ARCHIVED=$((ARCHIVED+1))
    fi
done < <(find "$MEMORY_DIR" -maxdepth 1 -name "*.md" -print0)

cat > "$REPORT_FILE" << EOF
# GC Report - $(date +%Y-%m-%d)

## 温度分布
- 🔥 热数据: $HOT
- 🟡 温数据: $WARM  
- ❄️ 冷数据(已归档): $COLD

## 操作
- 归档文件数: $ARCHIVED

EOF

echo "=== Memory GC Completed: $(date) ===" | tee -a "$LOG_FILE"
echo "归档: $ARCHIVED 个文件 | 热:$HOT 温:$WARM 冷:$COLD"
""")

# nightly-reflection.sh
(scripts_dir / "nightly-reflection.sh").write_text(r"""#!/bin/bash
# nightly-reflection.sh - 夜间反思脚本
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"
MEMORY_DIR="$WORKSPACE/memory"
REFLECTION_DIR="$MEMORY_DIR/reflections"
TODAY=$(date +%Y-%m-%d)
LOG_FILE="$WORKSPACE/logs/nightly-reflection.log"

mkdir -p "$REFLECTION_DIR" "$WORKSPACE/logs"

echo "=== Nightly Reflection: $(date) ===" | tee -a "$LOG_FILE"

# 检查 MEMORY.md 大小
MEMORY_SIZE=$(stat -c %s "$WORKSPACE/MEMORY.md" 2>/dev/null || echo 0)
MEMORY_KB=$(echo "scale=1; $MEMORY_SIZE / 1024" | bc)

# 统计热温冷数据
NOW=$(date +%s)
HOT=0; WARM=0; COLD=0

while IFS= read -r -d '' file; do
    filename=$(basename "$file")
    if [[ ! "$filename" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$ ]]; then
        continue
    fi
    FMTIME=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)
    AGE=$(( (NOW - FMTIME) / 86400 ))
    if [ "$AGE" -lt 7 ]; then HOT=$((HOT+1))
    elif [ "$AGE" -le 30 ]; then WARM=$((WARM+1))
    else COLD=$((COLD+1))
    fi
done < <(find "$MEMORY_DIR" -maxdepth 1 -name "*.md" -print0)

REFLECTION_FILE="$REFLECTION_DIR/$TODAY-nightly.md"
cat > "$REFLECTION_FILE" << EOF
# 夜间反思 $TODAY

## 系统健康度
- MEMORY.md 大小: ${MEMORY_KB}KB
- 🔥 热数据: $HOT
- 🟡 温数据: $WARM
- ❄️ 冷数据: $COLD

## CRUD 验证
- 写入测试: ✅
- 读取测试: ✅

## 待归档
- 冷数据数量: $COLD (如 >0，建议运行 memory-gc.sh)

EOF

echo "反思完成: $REFLECTION_FILE" | tee -a "$LOG_FILE"
""")

# extract-skill.sh
(scripts_dir / "extract-skill.sh").write_text(r"""#!/bin/bash
# extract-skill.sh - 从教训提取技能
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"
LESSON_NAME="${1:-}"
SKILL_NAME="${2:-$LESSON_NAME}"

if [ -z "$LESSON_NAME" ]; then
    echo "Usage: $0 <lesson-name> [skill-name]"
    exit 1
fi

LESSON_FILE="$WORKSPACE/memory/lessons/$LESSON_NAME.md"
SKILL_DIR="$WORKSPACE/skills/$SKILL_NAME"
SKILL_FILE="$SKILL_DIR/SKILL.md"

if [ ! -f "$LESSON_FILE" ]; then
    echo "ERROR: Lesson file not found: $LESSON_FILE"
    exit 1
fi

mkdir -p "$SKILL_DIR"

# Extract title from lesson frontmatter
TITLE=$(grep '^title:' "$LESSON_FILE" | head -1 | sed 's/title: *//;s/"//g')
DATE=$(date +%Y-%m-%d)
LESSON_ID=$(grep '^lesson_id:' "$LESSON_FILE" | head-1 | sed 's/lesson_id: *//' || echo "unknown")

cat > "$SKILL_FILE" << EOF
---
name: $SKILL_NAME
version: 1.0.0
description: "从教训提炼的技能: $TITLE"
source_lesson: $LESSON_NAME
extracted_date: $DATE
---

# $TITLE

## 技能说明
从教训 \`$LESSON_NAME\` 中提炼。

## 使用场景
TODO: 描述适用场景

## 步骤
TODO: 填写具体步骤

## 注意事项
TODO: 填写注意事项

## 参考
- 原始教训: memory/lessons/$LESSON_NAME.md
EOF

echo "✅ 技能已生成: $SKILL_FILE"
echo "请手动完善 SKILL.md 内容"
""")

# Make scripts executable
for script in scripts_dir.iterdir():
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# Also create symlink/copy in workspace scripts/ for easier access as per SKILL.md usage
local_scripts = WORKSPACE / "scripts"
local_scripts.mkdir(exist_ok=True)
import shutil
for script in scripts_dir.iterdir():
    dest = local_scripts / script.name
    shutil.copy2(script, dest)
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Distractor files ──────────────────────────────────────────────────────────
write("logs/.gitkeep", "")
write(".openclaw/config.yaml", """workspace: /workspace
agent_name: DevOpsBot
version: 1.0.0
""")
write("skills/.gitkeep", "")
write("memory/.archive/.gitkeep", "")

# Fake old archive from before (distractor)
old_archive_month = (today - timedelta(days=90)).strftime("%Y-%m")
write(f"memory/.archive/{old_archive_month}/2024-09-01.md", """# 2024-09-01

## 完成
- [初始化内存系统]
""")

print("✅ Workspace generated successfully.")
print(f"Cold daily logs: {len(cold_dates)} files (45-62 days old)")
print(f"Warm daily logs: {len(warm_dates)} files (10-18 days old)")
print(f"Today's log: {today.strftime('%Y-%m-%d')}.md")