#!/bin/bash
# Memory Search - 在加载的记忆中搜索
# 用法：bash scripts/memory-search.sh "搜索关键词"

WORKSPACE_DIR="$HOME/.openclaw/workspace"
SESSION_STATE="$WORKSPACE_DIR/SESSION-STATE.md"

if [ -z "$1" ]; then
    echo "用法：bash scripts/memory-search.sh \"搜索关键词\""
    echo "例如：bash scripts/memory-search.sh \"CSS 框架\""
    exit 1
fi

QUERY="$1"

echo "🔍 搜索记忆：$QUERY"
echo "=============================="
echo ""

# 检查 SESSION-STATE.md 是否存在
if [ ! -f "$SESSION_STATE" ]; then
    echo "⚠️  记忆未加载，先运行：bash scripts/memory-loader.sh"
    exit 1
fi

# 搜索并显示结果（带上下文）
RESULTS=$(grep -inC 3 "$QUERY" "$SESSION_STATE" 2>/dev/null)

if [ -z "$RESULTS" ]; then
    echo "📭 未找到相关记忆"
    echo ""
    echo "尝试以下关键词："
    grep -io "[A-Za-z0-9_]\{3,\}" "$SESSION_STATE" | sort | uniq -c | sort -rn | head -10
    exit 0
fi

# 显示结果
echo "$RESULTS" | head -50

echo ""
echo "=============================="
echo "💡 提示：可以用 grep -inC 5 查看更多上下文"
