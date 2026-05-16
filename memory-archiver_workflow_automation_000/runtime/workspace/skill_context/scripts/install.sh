#!/bin/bash
# Memory Archiver Skill - 安装脚本
# 用法：bash skills/memory-archiver/scripts/install.sh
#
# 功能：
# 1. 创建记忆目录结构
# 2. 安装 auto-memory-search hook（自动注册到 OpenClaw）
# 3. 自动添加 cron 任务

set -e

WORKSPACE="${HOME}/.openclaw/workspace"
SKILL_DIR="${WORKSPACE}/skills/memory-archiver"
HOOKS_DIR="${WORKSPACE}/hooks/auto-memory-search"
MEMORY_DAILY="${WORKSPACE}/memory/daily"
MEMORY_WEEKLY="${WORKSPACE}/memory/weekly"

echo "🔧 开始安装 Memory Archiver Skill..."
echo ""

# ===== Step 1: 创建记忆目录 =====
echo "📁 Step 1: 创建记忆目录..."
mkdir -p "$MEMORY_DAILY" "$MEMORY_WEEKLY"
echo "   ✅ memory/daily/"
echo "   ✅ memory/weekly/"
echo ""

# ===== Step 2: 安装 auto-memory-search hook =====
echo "🔍 Step 2: 安装 auto-memory-search hook..."

HOOK_SOURCE="${SKILL_DIR}/hooks"

if [ ! -f "${HOOK_SOURCE}/handler.js" ] || [ ! -f "${HOOK_SOURCE}/HOOK.md" ]; then
    echo "   ❌ Hook 源文件不存在：${HOOK_SOURCE}/"
    echo "   请确认 skills/memory-archiver/hooks/ 下有 handler.js 和 HOOK.md"
    exit 1
fi

# 复制 hook 文件到 workspace/hooks/
mkdir -p "$HOOKS_DIR"
cp "${HOOK_SOURCE}/handler.js" "${HOOKS_DIR}/handler.js"
cp "${HOOK_SOURCE}/HOOK.md" "${HOOKS_DIR}/HOOK.md"
echo "   ✅ Hook 文件已复制到 ${HOOKS_DIR}/"

# 尝试通过 openclaw hooks install 正式注册
if command -v openclaw &> /dev/null; then
    # 检查是否已安装
    if openclaw hooks list 2>/dev/null | grep -q "auto-memory-search"; then
        echo "   ✅ Hook 已注册（跳过重复安装）"
    else
        echo "   📦 正在注册 hook..."
        # 先清理可能存在的旧安装
        rm -rf "${HOME}/.openclaw/hooks/auto-memory-search" 2>/dev/null || true
        if openclaw hooks install --link "${HOOKS_DIR}" 2>/dev/null; then
            echo "   ✅ Hook 已通过 openclaw hooks install 注册"
        else
            echo "   ⚠️  自动注册失败，请手动执行："
            echo "      openclaw hooks install --link ~/.openclaw/workspace/hooks/auto-memory-search"
        fi
    fi

    # 提示重启 gateway
    echo ""
    echo "   💡 重启 gateway 生效："
    echo "      systemctl --user restart openclaw-gateway.service"
else
    echo "   ⚠️  未检测到 openclaw CLI，请手动注册 hook："
    echo "      openclaw hooks install --link ~/.openclaw/workspace/hooks/auto-memory-search"
fi

echo ""

# ===== Step 3: 自动添加 Cron 任务 =====
echo "⏰ Step 3: 添加 Cron 任务..."
echo ""

# 检查 cron 任务是否已存在
CRON_LIST=$(openclaw cron list 2>/dev/null | grep -c "记忆" 2>/dev/null || echo "0")
CRON_LIST=$(echo "$CRON_LIST" | tr -d '[:space:]')  # 清理空白字符

# 确保是有效数字
if ! [[ "$CRON_LIST" =~ ^[0-9]+$ ]]; then
    CRON_LIST=0
fi

if [ "$CRON_LIST" -ge 3 ]; then
    echo "   ✅ Cron 任务已存在（跳过添加）"
else
    echo "   📅 正在添加记忆及时写入 (10 分钟)..."
    if openclaw cron add --name "记忆及时写入" --schedule '{"kind":"every","everyMs":600000}' --payload '{"kind":"systemEvent","text":"📝 记忆及时写入检查（静默模式）"}' --session-target main --delivery '{"mode":"none"}' 2>/dev/null; then
        echo "   ✅ 已添加"
    else
        echo "   ⚠️  添加失败（可能已存在）"
    fi

    echo "   📅 正在添加记忆归档 - Daily (每天 23:00)..."
    if openclaw cron add --name "记忆归档 - Daily" --schedule '{"kind":"cron","expr":"0 23 * * *","tz":"Asia/Shanghai"}' --payload '{"kind":"systemEvent","text":"🌙 每日记忆归档时间（23:00）！"}' --session-target main --delivery '{"mode":"none"}' 2>/dev/null; then
        echo "   ✅ 已添加"
    else
        echo "   ⚠️  添加失败（可能已存在）"
    fi

    echo "   📅 正在添加记忆总结 - Weekly (每周日 22:00)..."
    if openclaw cron add --name "记忆总结 - Weekly" --schedule '{"kind":"cron","expr":"0 22 * * 0","tz":"Asia/Shanghai"}' --payload '{"kind":"systemEvent","text":"📅 每周记忆总结时间（周日 22:00）！"}' --session-target main --delivery '{"mode":"none"}' 2>/dev/null; then
        echo "   ✅ 已添加"
    else
        echo "   ⚠️  添加失败（可能已存在）"
    fi
fi

echo ""

# ===== 完成 =====
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Memory Archiver 安装完成！"
echo ""
echo "   📂 记忆目录：~/.openclaw/workspace/memory/"
echo "   🔍 Hook: ~/.openclaw/workspace/hooks/auto-memory-search/"
echo "   📖 文档：skills/memory-archiver/SKILL.md"
echo "   ⏰ Cron: 3 个定时任务已配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
