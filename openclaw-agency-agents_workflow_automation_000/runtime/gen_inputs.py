#!/usr/bin/env python3
"""
Generate the sandbox workspace for the openclaw-agency-agents skill evaluation.
Creates the skill directory structure with mock scripts, distractor files,
and an initial (unconfigured) state that the agent must configure.
"""

import os
import stat
from pathlib import Path

HOME = Path.home()
SKILL_BASE = HOME / ".openclaw" / "workspace" / "skills" / "openclaw-agency-agents"
SCRIPTS_DIR = SKILL_BASE / "scripts"
BACKUPS_DIR = SKILL_BASE / "backups"
REPO_DIR = SKILL_BASE / "repo"

# Create all directories
for d in [SKILL_BASE, SCRIPTS_DIR, BACKUPS_DIR, REPO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Distractor files in workspace ──────────────────────────────────────────────
distractor_root = Path("/workspace")
distractor_root.mkdir(exist_ok=True)

distractor_files = {
    "project_brief.txt": "Q3 2024 Campaign Brief\nTarget: Cross-border e-commerce expansion\nPlatforms: TikTok, Instagram, Amazon\n",
    "meeting_notes.md": "## Sync Notes\n- Discussed persona switching for AI assistant\n- Need cross-border e-commerce specialist\n- Follow up on rollback procedure\n",
    "config_draft.yaml": "version: 1\nteam: product\nregion: APAC\n# TODO: finalize agent selection\n",
    "agents_wishlist.txt": "Agents we might need:\n- Someone for cross-border ops\n- Product manager persona\n- SEO person\n",
    "logs/app.log": "2024-01-15 09:00:01 INFO  system started\n2024-01-15 09:01:22 WARN  no active agent configured\n2024-01-15 09:05:44 ERROR config not found\n",
    "logs/error.log": "ImportError: no agent persona loaded\nTraceback: config missing at expected path\n",
    "tmp/scratch.json": '{"status": "draft", "agent": null, "timestamp": "2024-01-15T09:00:00Z"}\n',
    "tmp/old_backup.tar.gz.fake": "THIS IS NOT A REAL BACKUP - distractor file\n",
    "docs/onboarding.md": "# Team Onboarding\nWelcome to the product team.\nYou will be using an AI assistant platform.\nPlease ask your team lead for setup instructions.\n",
    "docs/platform_overview.txt": "AI Assistant Platform v2.3\n==========================\nThe platform supports multiple specialist personas.\nPersonas can be activated, searched, and reverted.\nContact IT for credential issues.\n",
    "src/placeholder.py": "# placeholder — not part of the agent skill\nprint('hello world')\n",
    "src/utils.py": "# utility stubs\ndef noop(): pass\n",
}

for rel_path, content in distractor_files.items():
    full_path = distractor_root / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# ── Agent catalogue (embedded in list.sh / search.sh) ─────────────────────────
# We store a canonical agent list in the skill base so scripts can reference it.
AGENTS_DATA = """工程部|前端开发者
工程部|后端架构师
工程部|AI工程师
工程部|DevOps自动化
工程部|安全工程师
工程部|快速原型师
工程部|高级开发者
工程部|移动应用开发者
工程部|数据工程师
工程部|技术文档工程师
工程部|自主优化架构师
工程部|嵌入式固件工程师
工程部|故障响应指挥官
工程部|威胁检测工程师
工程部|Solidity智能合约工程师
工程部|微信小程序开发者
工程部|代码审查员
工程部|数据库优化师
工程部|Git工作流大师
工程部|软件架构师
工程部|SRE
工程部|AI数据修复工程师
工程部|飞书集成开发工程师
工程部|钉钉集成开发工程师
设计部|UI设计师
设计部|UX研究员
设计部|UX架构师
设计部|品牌守护者
设计部|图像提示词工程师
设计部|视觉叙事师
设计部|趣味注入师
设计部|包容性视觉专家
营销部|小红书运营
营销部|抖音策略师
营销部|微信公众号运营
营销部|B站内容策略师
营销部|快手策略师
营销部|中国电商运营师
营销部|电商运营师
营销部|百度SEO专家
营销部|私域流量运营师
营销部|直播电商主播教练
营销部|跨境电商运营专家
营销部|短视频剪辑指导师
营销部|微博运营策略师
营销部|播客内容策略师
营销部|微信视频号运营策略师
营销部|知识付费产品策划师
营销部|小红书专家
营销部|微信公众号管理
营销部|知乎策略师
出海营销部|TikTok策略师
出海营销部|Twitter互动官
出海营销部|Instagram策展师
出海营销部|Reddit社区运营
出海营销部|应用商店优化师
付费媒体部|付费媒体审计师
付费媒体部|广告创意策略师
付费媒体部|社交广告策略师
付费媒体部|PPC竞价策略师
付费媒体部|程序化广告采买专家
付费媒体部|搜索词分析师
付费媒体部|追踪与归因专家
销售部|获客策略师
销售部|成交专家
销售部|客户成功经理
销售部|销售赋能师
销售部|大客户经理
销售部|渠道经理
产品部|产品经理
产品部|产品策略师
产品部|定价策略师
产品部|用户研究员
产品部|产品增长经理
产品部|数据驱动产品经理
其他|学术写作
其他|法律顾问
其他|财务分析师
其他|人力资源专家
其他|项目经理
其他|供应链专家
其他|测试工程师
其他|客户支持专家
其他|空间计算专家
其他|专业顾问
"""

agents_file = SKILL_BASE / "agents.db"
agents_file.write_text(AGENTS_DATA.strip(), encoding="utf-8")

# ── Active config (starts as unconfigured) ────────────────────────────────────
active_config = SKILL_BASE / "active_agent.conf"
# Intentionally NOT creating this file — setup.sh should initialize it.

# ── setup.sh ──────────────────────────────────────────────────────────────────
setup_sh = SCRIPTS_DIR / "setup.sh"
setup_sh.write_text(r"""#!/usr/bin/env bash
# setup.sh — Initialize the openclaw-agency-agents environment
set -euo pipefail

SKILL_BASE="$HOME/.openclaw/workspace/skills/openclaw-agency-agents"
REPO_DIR="$SKILL_BASE/repo"
BACKUPS_DIR="$SKILL_BASE/backups"
ACTIVE_CONFIG="$SKILL_BASE/active_agent.conf"
AGENTS_DB="$SKILL_BASE/agents.db"

mkdir -p "$REPO_DIR" "$BACKUPS_DIR"

# Initialize active config if it does not exist
if [ ! -f "$ACTIVE_CONFIG" ]; then
    echo "agent=none" > "$ACTIVE_CONFIG"
    echo "activated_at=" >> "$ACTIVE_CONFIG"
    echo "[setup] Initialized active_agent.conf"
fi

# Create a minimal repo structure to simulate cloned repo
if [ ! -f "$REPO_DIR/.initialized" ]; then
    touch "$REPO_DIR/.initialized"
    echo "repo_version=1.0.0" > "$REPO_DIR/repo.meta"
    echo "[setup] Repository initialized at $REPO_DIR"
fi

echo "[setup] openclaw-agency-agents is ready. $(wc -l < "$AGENTS_DB") agents available."
""", encoding="utf-8")

# ── activate.sh ───────────────────────────────────────────────────────────────
activate_sh = SCRIPTS_DIR / "activate.sh"
activate_sh.write_text(r"""#!/usr/bin/env bash
# activate.sh <智能体名称> — Activate a named agent persona
set -euo pipefail

SKILL_BASE="$HOME/.openclaw/workspace/skills/openclaw-agency-agents"
ACTIVE_CONFIG="$SKILL_BASE/active_agent.conf"
BACKUPS_DIR="$SKILL_BASE/backups"
AGENTS_DB="$SKILL_BASE/agents.db"

if [ $# -lt 1 ]; then
    echo "Usage: activate.sh <智能体名称>" >&2
    exit 1
fi

AGENT_NAME="$*"

# Verify agent exists in catalogue
if ! grep -qF "|${AGENT_NAME}" "$AGENTS_DB"; then
    echo "[error] Agent '${AGENT_NAME}' not found in catalogue." >&2
    echo "[hint]  Run search.sh to find available agents." >&2
    exit 2
fi

# Ensure active config exists (require setup to have been run)
if [ ! -f "$ACTIVE_CONFIG" ]; then
    echo "[error] System not initialized. Run setup.sh first." >&2
    exit 3
fi

# Auto-backup current configuration before switching
BACKUP_COUNT=$(ls -1 "$BACKUPS_DIR"/backup_*.conf 2>/dev/null | wc -l)
NEXT_BACKUP=$((BACKUP_COUNT + 1))
BACKUP_FILE="$BACKUPS_DIR/backup_${NEXT_BACKUP}.conf"
cp "$ACTIVE_CONFIG" "$BACKUP_FILE"
echo "[backup] Current config saved as backup_${NEXT_BACKUP}.conf"

# Write new active agent
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
{
    echo "agent=${AGENT_NAME}"
    echo "activated_at=${TIMESTAMP}"
} > "$ACTIVE_CONFIG"

echo "[activate] Agent '${AGENT_NAME}' is now active."
echo "[info] To revert, run: restore.sh ${NEXT_BACKUP}"
""", encoding="utf-8")

# ── list.sh ───────────────────────────────────────────────────────────────────
list_sh = SCRIPTS_DIR / "list.sh"
list_sh.write_text(r"""#!/usr/bin/env bash
# list.sh [分类] — List available agents, optionally filtered by category
set -euo pipefail

SKILL_BASE="$HOME/.openclaw/workspace/skills/openclaw-agency-agents"
AGENTS_DB="$SKILL_BASE/agents.db"

if [ ! -f "$AGENTS_DB" ]; then
    echo "[error] agents.db not found. Run setup.sh first." >&2
    exit 1
fi

CATEGORY="${1:-}"

if [ -z "$CATEGORY" ]; then
    echo "=== All Available Agents ==="
    awk -F'|' '{print NR". ["$1"] "$2}' "$AGENTS_DB"
else
    echo "=== Agents in: ${CATEGORY} ==="
    grep -F "${CATEGORY}" "$AGENTS_DB" | awk -F'|' '{print "- "$2}' || echo "(no matches)"
fi
""", encoding="utf-8")

# ── search.sh ─────────────────────────────────────────────────────────────────
search_sh = SCRIPTS_DIR / "search.sh"
search_sh.write_text(r"""#!/usr/bin/env bash
# search.sh <关键词> — Search agents by keyword
set -euo pipefail

SKILL_BASE="$HOME/.openclaw/workspace/skills/openclaw-agency-agents"
AGENTS_DB="$SKILL_BASE/agents.db"

if [ $# -lt 1 ]; then
    echo "Usage: search.sh <关键词>" >&2
    exit 1
fi

KEYWORD="$*"

if [ ! -f "$AGENTS_DB" ]; then
    echo "[error] agents.db not found. Run setup.sh first." >&2
    exit 1
fi

echo "=== Search results for: ${KEYWORD} ==="
RESULTS=$(grep -F "${KEYWORD}" "$AGENTS_DB" || true)
if [ -z "$RESULTS" ]; then
    echo "(no agents found matching '${KEYWORD}')"
else
    echo "$RESULTS" | awk -F'|' '{print "- ["$1"] "$2}'
fi
""", encoding="utf-8")

# ── restore.sh ────────────────────────────────────────────────────────────────
restore_sh = SCRIPTS_DIR / "restore.sh"
restore_sh.write_text(r"""#!/usr/bin/env bash
# restore.sh [备份编号] — Restore a previous agent configuration
set -euo pipefail

SKILL_BASE="$HOME/.openclaw/workspace/skills/openclaw-agency-agents"
ACTIVE_CONFIG="$SKILL_BASE/active_agent.conf"
BACKUPS_DIR="$SKILL_BASE/backups"

# List backups if no argument given
if [ $# -lt 1 ]; then
    echo "=== Available Backups ==="
    if ls "$BACKUPS_DIR"/backup_*.conf 2>/dev/null | head -1 > /dev/null 2>&1; then
        for f in "$BACKUPS_DIR"/backup_*.conf; do
            NUM=$(basename "$f" | sed 's/backup_\([0-9]*\)\.conf/\1/')
            CONTENT=$(cat "$f")
            echo "Backup ${NUM}: ${CONTENT}"
        done
    else
        echo "(no backups found)"
    fi
    echo ""
    echo "Usage: restore.sh <备份编号>"
    exit 0
fi

BACKUP_NUM="$1"
BACKUP_FILE="$BACKUPS_DIR/backup_${BACKUP_NUM}.conf"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "[error] Backup #${BACKUP_NUM} not found at ${BACKUP_FILE}" >&2
    exit 4
fi

# Save current state as a new backup before restoring
BACKUP_COUNT=$(ls -1 "$BACKUPS_DIR"/backup_*.conf 2>/dev/null | wc -l)
NEXT_BACKUP=$((BACKUP_COUNT + 1))
cp "$ACTIVE_CONFIG" "$BACKUPS_DIR/backup_${NEXT_BACKUP}.conf"

# Restore
cp "$BACKUP_FILE" "$ACTIVE_CONFIG"
RESTORED_AGENT=$(grep '^agent=' "$ACTIVE_CONFIG" | cut -d'=' -f2-)
echo "[restore] Restored backup #${BACKUP_NUM}. Active agent is now: '${RESTORED_AGENT}'"
""", encoding="utf-8")

# ── update.sh ─────────────────────────────────────────────────────────────────
update_sh = SCRIPTS_DIR / "update.sh"
update_sh.write_text(r"""#!/usr/bin/env bash
# update.sh — Pull the latest agent catalogue
set -euo pipefail
echo "[update] Simulating update check... (local environment, no remote pull needed)"
echo "[update] Agent catalogue is up to date."
""", encoding="utf-8")

# Make all scripts executable
for script in [setup_sh, activate_sh, list_sh, search_sh, restore_sh, update_sh]:
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Additional distractor files inside skill dir ───────────────────────────────
(SKILL_BASE / "CHANGELOG.txt").write_text(
    "v1.0.0 - Initial release\nv1.1.0 - Added 营销部 agents\nv1.2.0 - Cross-border e-commerce agents added\n",
    encoding="utf-8"
)
(SKILL_BASE / "notes_internal.txt").write_text(
    "Internal note: backup_0.conf does NOT exist by design.\nBackups start at backup_1.conf after first activation.\n"
    "Do not delete backups manually.\n",
    encoding="utf-8"
)
(SKILL_BASE / ".metadata.json").write_text(
    '{"skill_id": "openclaw-agency-agents", "version": "1.2.0", "total_agents": 86, "initialized": false}\n',
    encoding="utf-8"
)
(SKILL_BASE / "scripts" / "README_SCRIPTS.txt").write_text(
    "These scripts manage the openclaw agency agents lifecycle.\n"
    "Execution order for fresh setup: setup.sh -> list.sh/search.sh -> activate.sh\n"
    "Reverting changes: restore.sh [backup number]\n",
    encoding="utf-8"
)

print("✅ Sandbox workspace generated successfully.")
print(f"   Skill base: {SKILL_BASE}")
print(f"   Scripts:    {SCRIPTS_DIR}")
print(f"   Agents DB:  {agents_file} ({len(AGENTS_DATA.strip().splitlines())} agents)")
print(f"   Distractors: {len(distractor_files)} files in /workspace")