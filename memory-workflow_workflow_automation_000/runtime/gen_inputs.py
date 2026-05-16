import os
import stat
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/root/.openclaw/workspace")

# --- Create full directory structure ---
dirs = [
    workspace,
    workspace / "skills" / "memory-workflow" / "scripts",
    workspace / "skills" / "memory-workflow" / "templates",
    workspace / "memory",
    workspace / "logs",
    workspace / "skills" / "other-skill" / "scripts",
    workspace / "skills" / "another-skill",
    workspace / "data" / "portfolio",
    workspace / "data" / "reports",
    workspace / "archive" / "2025",
    workspace / "archive" / "2024",
    workspace / "tmp",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# --- daily-summary.sh (the real script as per SKILL.md behavior) ---
daily_summary_sh = workspace / "skills" / "memory-workflow" / "scripts" / "daily-summary.sh"
daily_summary_sh.write_text(r"""#!/bin/bash
# daily-summary.sh - 每日摘要脚本
# Checks for .daily-summary-pending marker file and creates daily note if not already present

WORKSPACE="/root/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"
PENDING_FILE="$WORKSPACE/.daily-summary-pending"
TIMESTAMP_FILE="$WORKSPACE/.daily-summary-timestamp"
LOG_FILE="$WORKSPACE/logs/daily-summary.log"
CONFIG_FILE="$HOME/.openclaw/workspace/.memory-workflow-config"

# Load config
KEEP_DAYS=7
SUMMARY_TIMEOUT_MINUTES=5

if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

TODAY=$(date +%Y-%m-%d)
NOW=$(date +"%Y-%m-%d %H:%M:%S")
DAILY_NOTE="$MEMORY_DIR/$TODAY.md"

echo "[$NOW] daily-summary.sh invoked" >> "$LOG_FILE"

# If pending marker does not exist, do nothing
if [ ! -f "$PENDING_FILE" ]; then
    echo "[$NOW] No pending marker found. Exiting." >> "$LOG_FILE"
    exit 0
fi

# If today's note already exists, remove marker and exit
if [ -f "$DAILY_NOTE" ]; then
    echo "[$NOW] Daily note already exists: $DAILY_NOTE. Removing marker." >> "$LOG_FILE"
    rm -f "$PENDING_FILE"
    exit 0
fi

# Create today's daily note from template
TEMPLATE="$WORKSPACE/skills/memory-workflow/templates/daily-note-template.md"
if [ -f "$TEMPLATE" ]; then
    sed "s/YYYY-MM-DD/$TODAY/g; s/YYYY-MM-DD HH:MM:SS/$NOW/g" "$TEMPLATE" > "$DAILY_NOTE"
else
    cat > "$DAILY_NOTE" << EOF
# $TODAY - 每日摘要

## 📋 今日重点
_待填充..._

## 💬 重要对话
_待填充..._

## 🎯 关键决策
_待填充..._

## 📝 待办更新
_待填充..._

---
*自动生成时间：$NOW*
*记录者：[助手名称]*
EOF
fi

echo "[$NOW] Created daily note: $DAILY_NOTE" >> "$LOG_FILE"
rm -f "$PENDING_FILE"
echo "[$NOW] Removed pending marker." >> "$LOG_FILE"

# Cleanup old notes
find "$MEMORY_DIR" -name "*.md" -mtime +$KEEP_DAYS -delete 2>/dev/null
echo "[$NOW] Cleaned up notes older than $KEEP_DAYS days." >> "$LOG_FILE"
""")
daily_summary_sh.chmod(daily_summary_sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# --- install.sh ---
install_sh = workspace / "skills" / "memory-workflow" / "scripts" / "install.sh"
install_sh.write_text(r"""#!/bin/bash
# install.sh - 安装配置脚本

WORKSPACE="/root/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs"
MEMORY_DIR="$WORKSPACE/memory"
CONFIG_FILE="$HOME/.openclaw/workspace/.memory-workflow-config"
SCRIPT_PATH="$WORKSPACE/skills/memory-workflow/scripts/daily-summary.sh"

# Create required directories
mkdir -p "$LOG_DIR" "$MEMORY_DIR"

# Create default config if not exists
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'EOF'
# Memory Workflow Configuration
DAILY_SUMMARY_HOUR=23
SUMMARY_TIMEOUT_MINUTES=5
ARCHIVE_FREQUENCY=new_session_only
KEEP_DAYS=7
EOF
    echo "Created default config: $CONFIG_FILE"
fi

# Install cron job
CRON_LINE="*/1 * * * * $SCRIPT_PATH >> $WORKSPACE/logs/daily-summary.log 2>&1"
( crontab -l 2>/dev/null | grep -v "daily-summary.sh" ; echo "$CRON_LINE" ) | crontab -
echo "Cron job installed: $CRON_LINE"
echo "Installation complete."
""")
install_sh.chmod(install_sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# --- weekly-review.sh ---
weekly_review_sh = workspace / "skills" / "memory-workflow" / "scripts" / "weekly-review.sh"
weekly_review_sh.write_text(r"""#!/bin/bash
# weekly-review.sh - 每周回顾脚本
echo "Weekly review triggered at $(date)"
""")
weekly_review_sh.chmod(weekly_review_sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# --- daily-note-template.md ---
template = workspace / "skills" / "memory-workflow" / "templates" / "daily-note-template.md"
template.write_text("""# YYYY-MM-DD - 每日摘要

## 📋 今日重点
_待填充..._

## 💬 重要对话
_待填充..._

## 🎯 关键决策
_待填充..._

## 📝 待办更新
_待填充..._

---
*自动生成时间：YYYY-MM-DD HH:MM:SS*
*记录者：[助手名称]*
""")

# --- Distractor files ---
(workspace / "data" / "portfolio" / "holdings_2025Q4.csv").write_text(
    "ticker,shares,price\nAAPL,100,182.5\nMSFT,50,415.0\nNVDA,30,875.2\n"
)
(workspace / "data" / "portfolio" / "risk_report.txt").write_text(
    "Portfolio Beta: 1.12\nSharpe Ratio: 1.45\nMax Drawdown: -8.3%\n"
)
(workspace / "data" / "reports" / "monthly_summary_2025_12.md").write_text(
    "# Monthly Summary December 2025\nRevenue: $1.2M\nExpenses: $0.8M\n"
)
(workspace / "archive" / "2025" / "q1_notes.md").write_text("# Q1 2025 Notes\nOld archived content.\n")
(workspace / "archive" / "2024" / "year_end.md").write_text("# 2024 Year End\nLegacy archive.\n")
(workspace / "tmp" / "scratch.txt").write_text("temporary file - ignore\n")
(workspace / "skills" / "other-skill" / "scripts" / "run.sh").write_text("#!/bin/bash\necho 'other skill'\n")
(workspace / "skills" / "another-skill" / "README.txt").write_text("Another skill placeholder.\n")

# --- Stale/messy logs (distractor) ---
(workspace / "logs" / "old-cron.log").write_text(
    "[2025-12-01 23:01:00] old log entry\n[2025-12-02 23:01:00] old log entry\n"
)

# --- A broken/incomplete old MEMORY.md as distractor (wrong format, outdated) ---
old_memory = workspace / "MEMORY.md"
old_memory.write_text("""# Memory File

Last updated: 2025-11-30

## User
Name: Alex Chen
Role: Portfolio Manager

## notes
- likes coffee
- old preference: prefers emails
""")

# --- Old daily notes that should be cleaned up (older than KEEP_DAYS=14 target) ---
for days_ago in [20, 25, 30]:
    old_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    old_note = workspace / "memory" / f"{old_date}.md"
    old_note.write_text(f"# {old_date} - 每日摘要\n\n## 📋 今日重点\nOld content.\n")

print("Workspace generated successfully.")
print(f"Workspace root: {workspace}")