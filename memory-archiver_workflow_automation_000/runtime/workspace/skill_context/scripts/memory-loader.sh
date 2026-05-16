#!/bin/bash
# Memory Loader - 加载三层记忆到 SESSION-STATE.md
# 用法：bash scripts/memory-loader.sh

WORKSPACE_DIR="$HOME/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE_DIR/memory"
SESSION_STATE="$WORKSPACE_DIR/SESSION-STATE.md"

echo "📚 加载三层记忆..."

# 创建 SESSION-STATE.md 头部
cat > "$SESSION_STATE" << 'EOF'
# SESSION-STATE.md - 会话记忆缓存

> 自动加载的三层记忆内容（用于快速搜索）
> 最后更新：TIMESTAMP

---

## 📋 记忆索引

EOF

# 更新时间戳
sed -i "s/TIMESTAMP/$(date '+%Y-%m-%d %H:%M')/" "$SESSION_STATE"

# 1. 加载今日记忆
TODAY=$(date +%Y-%m-%d)
if [ -f "$MEMORY_DIR/daily/$TODAY.md" ]; then
    echo "✅ 加载今日记忆：$TODAY.md"
    echo "" >> "$SESSION_STATE"
    echo "## 📅 今日记忆 ($TODAY)" >> "$SESSION_STATE"
    echo "" >> "$SESSION_STATE"
    cat "$MEMORY_DIR/daily/$TODAY.md" >> "$SESSION_STATE"
    echo "" >> "$SESSION_STATE"
else
    echo "⚠️  今日记忆文件不存在"
fi

# 2. 加载昨日记忆
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d 2>/dev/null)
if [ -n "$YESTERDAY" ] && [ -f "$MEMORY_DIR/daily/$YESTERDAY.md" ]; then
    echo "✅ 加载昨日记忆：$YESTERDAY.md"
    echo "" >> "$SESSION_STATE"
    echo "## 📅 昨日记忆 ($YESTERDAY)" >> "$SESSION_STATE"
    echo "" >> "$SESSION_STATE"
    cat "$MEMORY_DIR/daily/$YESTERDAY.md" >> "$SESSION_STATE"
    echo "" >> "$SESSION_STATE"
fi

# 3. 加载最近 3 天的 daily 记忆
echo "✅ 加载最近 3 天的 daily 记忆..."
for file in $(ls -t "$MEMORY_DIR/daily/"*.md 2>/dev/null | head -3); do
    filename=$(basename "$file")
    if [ "$filename" != "$TODAY.md" ] && [ "$filename" != "$YESTERDAY.md" ]; then
        echo "  - $filename"
        echo "" >> "$SESSION_STATE"
        echo "## 📅 $filename" >> "$SESSION_STATE"
        echo "" >> "$SESSION_STATE"
        head -50 "$file" >> "$SESSION_STATE"
        echo "" >> "$SESSION_STATE"
    fi
done

# 4. 加载 MEMORY.md（长期记忆）
if [ -f "$WORKSPACE_DIR/MEMORY.md" ]; then
    echo "✅ 加载长期记忆：MEMORY.md"
    echo "" >> "$SESSION_STATE"
    echo "## 📚 长期记忆 (MEMORY.md)" >> "$SESSION_STATE"
    echo "" >> "$SESSION_STATE"
    head -150 "$WORKSPACE_DIR/MEMORY.md" >> "$SESSION_STATE"
    echo "" >> "$SESSION_STATE"
fi

# 5. 加载最近一周的 weekly 记忆
echo "✅ 加载 weekly 记忆..."
for file in $(ls -t "$MEMORY_DIR/weekly/"*.md 2>/dev/null | head -2); do
    filename=$(basename "$file")
    echo "  - $filename"
    echo "" >> "$SESSION_STATE"
    echo "## 📆 $filename" >> "$SESSION_STATE"
    echo "" >> "$SESSION_STATE"
    head -80 "$file" >> "$SESSION_STATE"
    echo "" >> "$SESSION_STATE"
done

# 统计
echo ""
echo "📊 加载完成!"
echo "   SESSION-STATE.md 大小：$(wc -l < "$SESSION_STATE") 行"
echo "   文件位置：$SESSION_STATE"
