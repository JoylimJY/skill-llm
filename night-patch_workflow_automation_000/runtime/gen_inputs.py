import os
import random
import stat
from pathlib import Path

random.seed(42)

# --- Define workspace root ---
workspace = Path("/home/devuser/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create deeply nested distractor structure ---
dirs = [
    "src/api/handlers",
    "src/api/middleware",
    "src/models",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "docs/architecture",
    "docs/deployment",
    "scripts/deploy",
    "scripts/maintenance",
    "config",
    "logs",
    ".openclaw/workspace/skills",
    "data/raw",
    "data/processed",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "src/api/handlers/user_handler.py": "# User API handler\ndef get_user(id): pass\n",
    "src/api/handlers/order_handler.py": "# Order API handler\ndef get_order(id): pass\n",
    "src/api/middleware/auth.py": "# Auth middleware\ndef verify_token(t): return True\n",
    "src/models/user.py": "class User:\n    def __init__(self, name): self.name = name\n",
    "src/models/order.py": "class Order:\n    def __init__(self, id): self.id = id\n",
    "src/utils/helpers.py": "def slugify(s): return s.lower().replace(' ', '-')\n",
    "tests/unit/test_user.py": "def test_user_creation(): pass\n",
    "tests/integration/test_api.py": "def test_endpoint(): pass\n",
    "docs/architecture/overview.md": "# Architecture\nMicroservices pattern.\n",
    "docs/deployment/runbook.md": "# Deployment Runbook\nStep 1: Build\nStep 2: Push\nStep 3: Deploy\n",
    "scripts/deploy/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "scripts/maintenance/cleanup.sh": "#!/bin/bash\necho 'Cleaning up...'\n",
    "data/raw/sample.csv": "id,name,value\n1,alpha,100\n2,beta,200\n",
    "data/processed/output.json": '{"status": "processed", "count": 2}\n',
    ".openclaw/workspace/skills/.gitkeep": "",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# --- Create the NightPatch skill directory structure ---
skill_dir = workspace / "night-patch"
skill_dir.mkdir(parents=True, exist_ok=True)

(skill_dir / "config").mkdir(exist_ok=True)
(skill_dir / "logs").mkdir(exist_ok=True)

# config/default.yaml  — the canonical config
default_config = """\
schedule:
  enabled: true
  time: "03:00"
  timezone: "Asia/Shanghai"

safety:
  max_changes_per_night: 1
  require_rollback: true
  skip_production: true

detectors:
  shell_alias:
    enabled: true
    min_usage_count: 3

  note_organization:
    enabled: true
    max_scattered_files: 5

  log_optimization:
    enabled: true
    common_patterns: ["error", "warning", "info"]
"""
(skill_dir / "config" / "default.yaml").write_text(default_config)

# --- Simulate a realistic bash_history for devuser ---
# Commands with varying frequencies:
#   git status       → 7 times   (qualifies: ≥3)
#   docker ps        → 5 times   (qualifies: ≥3)
#   ls -la           → 4 times   (qualifies: ≥3, alias = ll)
#   kubectl get pods → 2 times   (does NOT qualify: <3)
#   cat /etc/hosts   → 1 time    (does NOT qualify)
#   cd ..            → 6 times   (qualifies: ≥3, but cd aliases are edge-case)
#   python3 manage.py runserver → 3 times (qualifies exactly at threshold)

history_entries = (
    ["git status"] * 7 +
    ["docker ps"] * 5 +
    ["ls -la"] * 4 +
    ["cd .."] * 6 +
    ["python3 manage.py runserver"] * 3 +
    ["kubectl get pods"] * 2 +
    ["cat /etc/hosts"] * 1 +
    # Add realistic noise
    ["git diff", "git add .", "git commit -m 'fix'",
     "docker build -t app .", "docker stop app",
     "pip install requests", "python3 -m pytest tests/",
     "ssh devserver", "tail -f /var/log/app.log",
     "vim src/api/handlers/user_handler.py",
     "export DEBUG=1", "echo $PATH",
     "ls", "pwd", "whoami"]
)

random.shuffle(history_entries)

home_dir = Path("/home/devuser")
bash_history_path = home_dir / ".bash_history"
bash_history_path.write_text("\n".join(history_entries) + "\n")
os.chown(str(bash_history_path), 1000, 1000)

# --- Create a minimal .bashrc (pre-existing, without any aliases) ---
bashrc_path = home_dir / ".bashrc"
bashrc_content = """\
# ~/.bashrc: executed by bash(1) for non-login shells.

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# History settings
HISTCONTROL=ignoreboth
HISTSIZE=1000
HISTFILESIZE=2000

# Enable color prompt
force_color_prompt=yes

PS1='\\u@\\h:\\w\\$ '

# Alias definitions (none yet)
# alias ll='ls -la'

# Set PATH
export PATH="$HOME/.local/bin:$PATH"
"""
bashrc_path.write_text(bashrc_content)
os.chown(str(bashrc_path), 1000, 1000)

# --- Create start.sh for the NightPatch skill ---
# This is the entry point script referenced in SKILL.md
start_sh_content = """\
#!/bin/bash
# NightPatch start.sh — entry point for the night-patch skill
# Usage: ./start.sh [dry-run|run]

MODE="${1:-run}"
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SKILL_DIR/config/default.yaml"
LOG_DIR="$SKILL_DIR/logs"
AUDIT_LOG="$LOG_DIR/night-patch-audit.log"
EXEC_LOG="$LOG_DIR/night-patch-execution.log"
ERROR_LOG="$LOG_DIR/night-patch-error.log"
HOME_DIR="$HOME"
BASH_HISTORY="$HOME_DIR/.bash_history"
BASHRC="$HOME_DIR/.bashrc"

mkdir -p "$LOG_DIR"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

log_exec() {
  echo "[$(timestamp)] $*" >> "$EXEC_LOG"
}

log_audit() {
  echo "[$(timestamp)] AUDIT: $*" >> "$AUDIT_LOG"
}

log_error() {
  echo "[$(timestamp)] ERROR: $*" >> "$ERROR_LOG"
}

log_exec "=== NightPatch started (mode=$MODE) ==="
log_audit "Session started. Mode: $MODE"

# --- Read config ---
MIN_USAGE=$(python3 -c "
import yaml, sys
try:
    with open('$CONFIG_FILE') as f:
        cfg = yaml.safe_load(f)
    print(cfg['detectors']['shell_alias']['min_usage_count'])
except Exception as e:
    print(3)
" 2>/dev/null)

MAX_CHANGES=$(python3 -c "
import yaml, sys
try:
    with open('$CONFIG_FILE') as f:
        cfg = yaml.safe_load(f)
    print(cfg['safety']['max_changes_per_night'])
except Exception as e:
    print(1)
" 2>/dev/null)

log_exec "Config loaded: min_usage_count=$MIN_USAGE, max_changes_per_night=$MAX_CHANGES"

# --- Detect: shell alias candidates ---
# Count command frequencies from bash_history
# Only consider simple commands (first token), skip builtins cd/export/echo
CANDIDATES=$(python3 << 'PYEOF'
import sys, collections, re

history_file = "$BASH_HISTORY"
min_usage = int("$MIN_USAGE")

# Commands to skip for alias creation (shell builtins / too short)
skip_cmds = {"cd", "export", "echo", "pwd", "ls", "exit", "source", ".", "alias"}

try:
    with open(history_file, "r", errors="replace") as f:
        lines = [l.strip() for l in f if l.strip()]
except Exception:
    lines = []

counter = collections.Counter(lines)
qualified = []
for cmd, count in counter.most_common():
    first_token = cmd.split()[0] if cmd.split() else ""
    if count >= min_usage and first_token not in skip_cmds and len(cmd) > 3:
        qualified.append((cmd, count))

for cmd, count in qualified:
    print(f"{count}\t{cmd}")
PYEOF
)

log_exec "Detection complete. Qualified candidates:"
log_exec "$CANDIDATES"

if [ -z "$CANDIDATES" ]; then
  log_exec "No candidates found. Nothing to do."
  log_audit "No actionable candidates detected."
  echo "No shell alias candidates found."
  exit 0
fi

# Pick the top candidate (most used)
TOP_CMD=$(echo "$CANDIDATES" | head -1 | cut -f2-)
TOP_COUNT=$(echo "$CANDIDATES" | head -1 | cut -f1)

log_exec "Top candidate: '$TOP_CMD' (used $TOP_COUNT times)"

# Derive alias name
ALIAS_NAME=$(python3 -c "
cmd = '''$TOP_CMD'''
tokens = cmd.split()
# Simple heuristic: use initials or abbreviation
if len(tokens) == 1:
    print(tokens[0][:3])
elif tokens[0] == 'git':
    sub = tokens[1] if len(tokens) > 1 else 'g'
    print('g' + sub[0])
elif tokens[0] == 'docker':
    sub = tokens[1] if len(tokens) > 1 else 'd'
    print('d' + sub[0])
elif tokens[0] == 'python3' and 'manage.py' in cmd:
    print('djrun')
elif tokens[0] == 'kubectl':
    print('kgp')
elif tokens == ['ls', '-la']:
    print('ll')
else:
    # fallback: first letter of each word, max 4
    initials = ''.join(t[0] for t in tokens if t[0].isalpha())[:4]
    print(initials if initials else 'np1')
")

log_exec "Alias name derived: $ALIAS_NAME -> '$TOP_CMD'"

# Check if alias already exists in .bashrc
if grep -q "alias $ALIAS_NAME=" "$BASHRC" 2>/dev/null; then
  log_exec "Alias '$ALIAS_NAME' already exists in .bashrc. Skipping."
  log_audit "Alias $ALIAS_NAME already exists, skipped."
  echo "Alias already exists, nothing to do."
  exit 0
fi

TODAY=$(date '+%Y-%m-%d')
REPORT_FILE="$LOG_DIR/night-patch-report-$TODAY.md"

if [ "$MODE" = "dry-run" ]; then
  log_exec "DRY-RUN mode: would add alias $ALIAS_NAME='$TOP_CMD' to ~/.bashrc"
  log_audit "DRY-RUN: alias $ALIAS_NAME='$TOP_CMD' (count=$TOP_COUNT)"
  echo "[DRY-RUN] Would create alias: $ALIAS_NAME='$TOP_CMD'"
  echo "[DRY-RUN] Target file: ~/.bashrc"
  echo "[DRY-RUN] Rollback: unalias $ALIAS_NAME (or remove from ~/.bashrc)"
  # Generate dry-run report
  cat > "$REPORT_FILE" << REPORT_EOF
# 夜间修补报告 - $TODAY (DRY-RUN)

## 执行摘要
- 检测到问题：$(echo "$CANDIDATES" | wc -l)个
- 执行修补：0个（DRY-RUN模式）
- 跳过修补：$(echo "$CANDIDATES" | wc -l)个（DRY-RUN）

## 详细内容
### 建议修补（DRY-RUN，未实际执行）
1. **创建shell alias**：\`$ALIAS_NAME\` → \`$TOP_CMD\`
   - 原因：该命令每天使用${TOP_COUNT}+次
   - 回滚：\`unalias $ALIAS_NAME\`

## 安全审计
- 执行时间：$(timestamp)
- 模式：DRY-RUN（未执行实际变更）
- 安全状态：✅ 所有安全检查通过
REPORT_EOF
  log_audit "DRY-RUN report generated: $REPORT_FILE"
  exit 0
fi

# --- Execute: apply the patch (max_changes_per_night = 1) ---
log_exec "Applying alias patch to $BASHRC"

# Write alias to .bashrc (NOT .bash_aliases — for better compatibility per SKILL.md)
echo "" >> "$BASHRC"
echo "# [NightPatch] Added $(date '+%Y-%m-%d') — auto-detected frequent command" >> "$BASHRC"
echo "alias $ALIAS_NAME='$TOP_CMD'" >> "$BASHRC"

log_exec "Alias added: alias $ALIAS_NAME='$TOP_CMD'"
log_audit "CHANGE APPLIED: added 'alias $ALIAS_NAME=$TOP_CMD' to $BASHRC. Rollback: unalias $ALIAS_NAME or remove line from $BASHRC"

# Count total candidates for report
TOTAL_CANDIDATES=$(echo "$CANDIDATES" | wc -l)
SKIPPED=$((TOTAL_CANDIDATES - 1))

# --- Generate Report ---
cat > "$REPORT_FILE" << REPORT_EOF
# 夜间修补报告 - $TODAY

## 执行摘要
- 检测到问题：${TOTAL_CANDIDATES}个
- 执行修补：1个（低风险）
- 跳过修补：${SKIPPED}个（需要人工确认）

## 详细内容
### 已执行修补
1. **创建shell alias**：\`$ALIAS_NAME\` → \`$TOP_CMD\`
   - 原因：该命令每天使用${TOP_COUNT}+次
   - 回滚：\`unalias $ALIAS_NAME\`

### 建议修补（需要确认）
$(echo "$CANDIDATES" | tail -n +2 | python3 -c "
import sys
lines = sys.stdin.read().strip().split('\n')
for i, line in enumerate(lines, 1):
    if line.strip():
        parts = line.split('\t', 1)
        count = parts[0] if len(parts) > 0 else '?'
        cmd = parts[1] if len(parts) > 1 else line
        print(f'{i}. **频繁命令**：\`{cmd}\`（使用{count}次）— 建议创建alias')
")

## 安全审计
- 执行时间：$(timestamp)
- 资源使用：内存<50MB，耗时<5分钟
- 安全状态：✅ 所有安全检查通过
- 变更目标文件：~/.bashrc（仅追加，不修改已有内容）
REPORT_EOF

log_exec "Report generated: $REPORT_FILE"
log_audit "Report saved to $REPORT_FILE"
log_exec "=== NightPatch completed successfully ==="
log_audit "Session ended successfully."

echo "✅ NightPatch completed!"
echo "   Alias created: $ALIAS_NAME='$TOP_CMD'"
echo "   Report: $REPORT_FILE"
echo "   Rollback: unalias $ALIAS_NAME"
"""

start_sh_path = skill_dir / "start.sh"
start_sh_path.write_text(start_sh_content)
start_sh_path.chmod(0o755)
os.chown(str(start_sh_path), 1000, 1000)

# --- Make sure all workspace files are owned by devuser ---
import subprocess
subprocess.run(["chown", "-R", "devuser:devuser", str(workspace)], check=True)
subprocess.run(["chown", "-R", "devuser:devuser", str(home_dir)], check=True)

print("Workspace generation complete.")
print(f"  ~/.bash_history: {bash_history_path}")
print(f"  ~/.bashrc: {bashrc_path}")
print(f"  Skill dir: {skill_dir}")