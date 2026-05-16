#!/bin/bash
# Auto Memory Search - 自动触发记忆搜索（多维度增强版）
# 用法：bash scripts/auto-memory-search.sh "用户消息"
# 功能：检测消息类型，多维度搜索相关记忆

USER_MESSAGE="$1"
WORKSPACE_DIR="$HOME/.openclaw/workspace"
SESSION_STATE="$WORKSPACE_DIR/SESSION-STATE.md"
MEMORY_DIR="$WORKSPACE_DIR/memory"
MEMORY_MD="$WORKSPACE_DIR/MEMORY.md"

# 检查缓存是否存在
if [ ! -f "$SESSION_STATE" ]; then
    echo "📚 记忆缓存不存在，先加载记忆..."
    bash "$WORKSPACE_DIR/skills/memory-archiver/scripts/memory-loader.sh" > /dev/null 2>&1
fi

# 检测消息类型和关键词
detect_type() {
    local msg="$1"
    local msg_lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    # 疑问类型
    if echo "$msg_lower" | grep -qE "怎么|如何|为什么|什么|哪里|何时|谁|哪个|能否|可以吗|行不行|what|how|why|where|when|who"; then
        echo "疑问"
        return 0
    fi
    
    # 修复类型
    if echo "$msg_lower" | grep -qE "修复|bug|错误|问题|故障|解决|repair|fix|error|issue|debug"; then
        echo "修复"
        return 0
    fi
    
    # 规范类型
    if echo "$msg_lower" | grep -qE "规范|规则|标准|要求|必须|应该|spec|standard|rule|require"; then
        echo "规范"
        return 0
    fi
    
    # 特征类型
    if echo "$msg_lower" | grep -qE "特征|特点|特性|特色|feature|characteristic"; then
        echo "特征"
        return 0
    fi
    
    # 配置类型
    if echo "$msg_lower" | grep -qE "配置|设置|安装|部署|环境|config|setup|install|deploy|environment"; then
        echo "配置"
        return 0
    fi
    
    # 命令类型
    if echo "$msg_lower" | grep -qE "命令|指令|脚本|用法|example|command|script|usage"; then
        echo "命令"
        return 0
    fi
    
    # 技术类型
    if echo "$msg_lower" | grep -qE "css|html|php|javascript|node|npm|tailwind|vite|thinkphp"; then
        echo "技术"
        return 0
    fi
    
    echo "普通"
    return 1
}

# 提取搜索关键词（多维度）
extract_keywords() {
    local msg="$1"
    # 英文单词
    echo "$msg" | grep -oE "[A-Za-z0-9_]{2,}" | head -5
    # 中文词语（按空格/标点分隔）
    echo "$msg" | sed 's/[[:space:]]\+/\n/g' | sed 's/[,.!?;:，。！？；：]\+/\n/g' | grep -E ".{2,}" | head -5
}

# 维度 1: 关键词搜索
search_by_keyword() {
    local keyword="$1"
    local file="$2"
    grep -inC 2 "$keyword" "$file" 2>/dev/null | head -20
}

# 维度 2: 类型标签搜索（[episodic], [semantic], [procedural]）
search_by_type() {
    local msg_type="$1"
    local file="$2"
    
    # 根据消息类型映射到记忆标签
    local type_tag=""
    case "$msg_type" in
        "修复"|"问题"|"错误") type_tag="procedural" ;;
        "配置"|"命令"|"技术") type_tag="semantic" ;;
        *) type_tag="episodic" ;;
    esac
    
    grep -inC 3 "\[$type_tag\]" "$file" 2>/dev/null | head -20
}

# 维度 3: 时间维度搜索（最近记忆优先）
search_by_time() {
    local keywords="$1"
    local results=""
    
    # 优先搜索今日记忆
    local today_file="$MEMORY_DIR/daily/$(date +%Y-%m-%d).md"
    if [ -f "$today_file" ]; then
        for kw in $keywords; do
            local result=$(grep -inC 2 "$kw" "$today_file" 2>/dev/null | head -10)
            if [ -n "$result" ]; then
                results="$results\n📍 今日记忆:\n---\n$result\n---\n"
            fi
        done
    fi
    
    # 搜索昨日记忆
    local yesterday=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d 2>/dev/null)
    local yesterday_file="$MEMORY_DIR/daily/$yesterday.md"
    if [ -f "$yesterday_file" ]; then
        for kw in $keywords; do
            local result=$(grep -inC 2 "$kw" "$yesterday_file" 2>/dev/null | head -10)
            if [ -n "$result" ]; then
                results="$results\n📍 昨日记忆:\n---\n$result\n---\n"
            fi
        done
    fi
    
    # 搜索长期记忆
    if [ -f "$MEMORY_MD" ]; then
        for kw in $keywords; do
            local result=$(grep -inC 2 "$kw" "$MEMORY_MD" 2>/dev/null | head -10)
            if [ -n "$result" ]; then
                results="$results\n📍 长期记忆:\n---\n$result\n---\n"
            fi
        done
    fi
    
    echo -e "$results"
}

# 维度 4: 组合搜索（多个关键词组合）
search_combined() {
    local keywords="$1"
    local file="$2"
    local results=""
    
    # 将关键词转换为 grep 正则（OR 关系）
    local pattern=$(echo "$keywords" | tr '\n' '|' | sed 's/|$//')
    if [ -n "$pattern" ]; then
        grep -inC 3 -E "$pattern" "$file" 2>/dev/null | head -25
    fi
}

# 主逻辑
echo "🔍 分析用户消息..."
MSG_TYPE=$(detect_type "$USER_MESSAGE")

if [ "$MSG_TYPE" == "普通" ]; then
    echo "ℹ️  普通消息，不自动搜索"
    exit 0
fi

echo "📋 消息类型：$MSG_TYPE"

# 提取关键词
KEYWORDS=$(extract_keywords "$USER_MESSAGE")

if [ -z "$KEYWORDS" ]; then
    echo "⚠️  未提取到关键词"
    exit 0
fi

echo "🔑 关键词：$(echo $KEYWORDS | tr '\n' ' ')"
echo ""

# 多维度搜索
echo "📚 启动多维度搜索..."
FOUND=0
ALL_RESULTS=""

# 维度 1: 关键词搜索（SESSION-STATE.md 缓存）
echo ""
echo "━━━ 维度 1: 关键词搜索 ━━━"
for keyword in $KEYWORDS; do
    RESULT=$(search_by_keyword "$keyword" "$SESSION_STATE")
    if [ -n "$RESULT" ]; then
        FOUND=1
        ALL_RESULTS="$ALL_RESULTS\n📌 关键词 \"$keyword\":\n---\n$RESULT\n---\n"
    fi
done

# 维度 2: 类型标签搜索
echo "━━━ 维度 2: 类型标签搜索 ━━━"
TYPE_RESULT=$(search_by_type "$MSG_TYPE" "$SESSION_STATE")
if [ -n "$TYPE_RESULT" ]; then
    FOUND=1
    ALL_RESULTS="$ALL_RESULTS\n📌 类型标签 [$MSG_TYPE] 相关:\n---\n$TYPE_RESULT\n---\n"
fi

# 维度 3: 时间维度搜索
echo "━━━ 维度 3: 时间维度搜索 ━━━"
TIME_RESULT=$(search_by_time "$KEYWORDS")
if [ -n "$TIME_RESULT" ]; then
    FOUND=1
    ALL_RESULTS="$ALL_RESULTS$TIME_RESULT"
fi

# 维度 4: 组合搜索
echo "━━━ 维度 4: 组合搜索 ━━━"
COMBINED_RESULT=$(search_combined "$KEYWORDS" "$SESSION_STATE")
if [ -n "$COMBINED_RESULT" ]; then
    FOUND=1
    ALL_RESULTS="$ALL_RESULTS\n📌 组合搜索结果:\n---\n$COMBINED_RESULT\n---\n"
fi

# 输出结果
if [ $FOUND -eq 0 ]; then
    echo "📭 未找到相关记忆"
else
    echo ""
    echo "✅ 多维度记忆搜索完成"
    echo ""
    echo -e "$ALL_RESULTS"
    echo ""
    echo "---"
    echo "以上记忆供参考，根据情况决定是否引用"
fi
