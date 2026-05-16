#!/bin/bash
# Memory Refresh - 智能刷新记忆缓存（检查后刷新）
# 用法：bash scripts/memory-refresh.sh

WORKSPACE_DIR="$HOME/.openclaw/workspace"
DAILY_FILE="$WORKSPACE_DIR/memory/daily/$(date +%Y-%m-%d).md"
SESSION_STATE="$WORKSPACE_DIR/SESSION-STATE.md"

echo "🔄 智能刷新记忆缓存..."

# 检查今日记忆文件是否存在
if [ ! -f "$DAILY_FILE" ]; then
    echo "⚠️  今日记忆文件不存在，跳过刷新"
    exit 0
fi

# 检查文件最后修改时间（是否在最近 10 分钟内）
MODIFIED_TIME=$(stat -c %Y "$DAILY_FILE" 2>/dev/null || stat -f %m "$DAILY_FILE" 2>/dev/null)
CURRENT_TIME=$(date +%s)
DIFF=$((CURRENT_TIME - MODIFIED_TIME))

if [ $DIFF -lt 600 ]; then
    echo "✅ 记忆文件在最近 10 分钟内已更新"
    echo "📚 重新加载三层记忆..."
    bash "$WORKSPACE_DIR/skills/memory-archiver/scripts/memory-loader.sh"
    echo ""
    echo "✅ 记忆缓存已刷新"
    echo "📊 缓存大小：$(wc -l < "$SESSION_STATE") 行"
else
    echo "⚠️ 记忆文件在最近 10 分钟内未更新，跳过刷新"
fi
