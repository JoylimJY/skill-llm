#!/usr/bin/env python3
import os
import random
import stat

random.seed(42)

workspace = "/workspace"

# ─── Directory structure ───────────────────────────────────────────────────────
dirs = [
    "knowledge-sync/scripts",
    "knowledge-sync/docs",
    "knowledge-sync/configs",
    "data/articles",
    "data/memory",
    "data/projects",
    "data/docs",
    "data/scripts",
    "data/learnings",
    "data/node_modules/some_pkg",
    "data/__pycache__",
    "data/.git/objects",
    "logs",
    "backups/weekly",
    "backups/monthly",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ─── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "knowledge-sync/docs/QUICKSTART.md": "# Quick Start\nRun the sync scripts to begin.\n",
    "knowledge-sync/docs/sync-guide.md": "# Sync Guide\nSee scripts for configuration.\n",
    "knowledge-sync/configs/old-config.conf": "# Deprecated config\nWATCH_DIR=/old/path\n",
    "knowledge-sync/configs/nutstore.conf": "# Nutstore config placeholder\nSYNC_INTERVAL=60\n",
    "logs/sync.log": "2026-03-15 10:00:01 INFO sync started\n2026-03-15 10:05:01 INFO push OK\n",
    "logs/git-pull.log": "2026-03-15 10:00:00 INFO pull started\nAlready up to date.\n",
    "backups/weekly/backup-2026-03-08.tar.gz.stub": "stub\n",
    "backups/monthly/backup-2026-03-01.tar.gz.stub": "stub\n",
    "tmp/scratch.tmp": "temp data\n",
    "data/articles/note1.md": "# Article 1\nContent here.\n",
    "data/memory/context.md": "# Memory\nAI context notes.\n",
    "data/projects/proj_alpha.md": "# Project Alpha\nIn progress.\n",
    "data/learnings/lesson1.md": "# Lesson 1\nWhat I learned.\n",
    "data/node_modules/some_pkg/index.js": "module.exports = {};\n",
    "data/__pycache__/module.cpython-39.pyc.stub": "bytecode stub\n",
}
for path, content in distractors.items():
    full = os.path.join(workspace, path)
    with open(full, "w") as f:
        f.write(content)

# ─── BROKEN sync-realtime.sh ──────────────────────────────────────────────────
# Missing: correct WATCH_DIRS, wrong EXCLUDE_PATTERN, wrong/missing DELAY, no proper loop
sync_realtime_broken = r"""#!/bin/bash
# Real-time sync script - INCOMPLETE CONFIGURATION
# TODO: Configure watch directories and exclude patterns

WORKSPACE="/workspace/data"

# FIXME: Only watching one directory - needs all required directories
WATCH_DIRS=(
    "$WORKSPACE/articles"
)

# FIXME: Exclude pattern is incomplete/wrong
EXCLUDE_PATTERN="node_modules"

# FIXME: Delay not set correctly
DELAY=60

echo "Starting realtime sync watcher..."
while true; do
    inotifywait -r -e modify,create,delete,move \
        --exclude "$EXCLUDE_PATTERN" \
        --timeout 30 \
        "${WATCH_DIRS[@]}" 2>/dev/null

    if [ $? -eq 0 ] || [ $? -eq 1 ]; then
        echo "[$(date)] Change detected, waiting ${DELAY}s before sync..."
        sleep "$DELAY"
        echo "[$(date)] Sync triggered."
    fi
done
"""

with open(os.path.join(workspace, "knowledge-sync/scripts/sync-realtime.sh"), "w") as f:
    f.write(sync_realtime_broken)

# ─── BROKEN git-auto-push.sh ──────────────────────────────────────────────────
# Missing: pull-before-push, no conflict detection, wrong commit message pattern
git_auto_push_broken = r"""#!/bin/bash
# Git auto-push script - INCOMPLETE

WORKSPACE="/workspace/data"
cd "$WORKSPACE" || exit 1

# FIXME: Missing git pull before push (causes conflicts)

# Add all changes
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "Nothing to commit."
    exit 0
fi

# Commit with timestamp
git commit -m "auto-backup: $(date '+%Y-%m-%d %H:%M:%S')"

# Push to remote
git push origin main

echo "Push complete."
"""

with open(os.path.join(workspace, "knowledge-sync/scripts/git-auto-push.sh"), "w") as f:
    f.write(git_auto_push_broken)

# ─── BROKEN git-auto-pull.sh ──────────────────────────────────────────────────
# Missing: --rebase flag, wrong branch
git_auto_pull_broken = r"""#!/bin/bash
# Git auto-pull script - INCOMPLETE

WORKSPACE="/workspace/data"
cd "$WORKSPACE" || exit 1

# FIXME: Missing --rebase flag, wrong branch name
git pull origin master

echo "Pull complete."
"""

with open(os.path.join(workspace, "knowledge-sync/scripts/git-auto-pull.sh"), "w") as f:
    f.write(git_auto_pull_broken)

# ─── Make scripts executable ──────────────────────────────────────────────────
for script in ["sync-realtime.sh", "git-auto-push.sh", "git-auto-pull.sh"]:
    path = os.path.join(workspace, "knowledge-sync/scripts", script)
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ─── Empty crontab config (to be created by agent) ────────────────────────────
# Intentionally leaving sync-crontab.txt absent - agent must CREATE it

# ─── SKILL.md copy in workspace ───────────────────────────────────────────────
skill_md_content = r"""---
name: knowledge-sync
version: 1.0.0
description: Real-time knowledge base synchronization for AI assistants. Supports inotifywait file monitoring, Git auto-push/pull, Nutstore sync, and multi-device consistency.
---

# Knowledge Sync - 知识库同步机制

> **核心原则**: Text > Brain，文件 > 记忆，同步 > 备份

## 🔧 核心功能

### 1. 实时同步

- ✅ inotifywait 文件监听
- ✅ 3-10 秒同步延迟
- ✅ 6 个目录监听（articles/memory/projects/docs/scripts/learnings）
- ✅ 自动排除（node_modules/__pycache__/.git）

### 2. Git 备份

- ✅ 每 5 分钟自动 push
- ✅ 每小时自动 pull
- ✅ 冲突检测和解决
- ✅ Gitee 远程备份

## 🔧 配置说明

### 监听目录配置

```bash
WATCH_DIRS=(
    "/path/to/workspace/articles"
    "/path/to/workspace/memory"
    "/path/to/workspace/projects"
    "/path/to/workspace/docs"
    "/path/to/workspace/scripts"
    "/path/to/workspace/learnings"
)
```

### 排除模式

```bash
EXCLUDE_PATTERN="\\.(log|tmp|swp|pyc)$|node_modules|__pycache__|\\.git"
```

## 📈 监控指标

| 指标 | 正常值 | 警告值 |
|------|--------|--------|
| 同步延迟 | <10 秒 | >30 秒 |
| Git push 间隔 | 5 分钟 | >10 分钟 |
| Git pull 间隔 | 1 小时 | >2 小时 |
| 冲突次数 | 0 | >1/周 |

## 🎓 最佳实践

### 1. 同步频率

- 实时同步：inotifywait 监听（3-10 秒）
- Git push：每 5 分钟
- Git pull：每小时

### 2. 冲突处理

- push 前先 pull
- 大改动分多次 commit
- 人工编辑前先 git pull

### Crontab 配置

```bash
# 每 5 分钟 Git push
*/5 * * * * /path/to/git-auto-push.sh

# 每小时 Git pull
0 * * * * cd /path/to/workspace && git pull origin main --rebase
```
"""
with open(os.path.join(workspace, "knowledge-sync/SKILL.md"), "w") as f:
    f.write(skill_md_content)

print("Workspace generated successfully.")