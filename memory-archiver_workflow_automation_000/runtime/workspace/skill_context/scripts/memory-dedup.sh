#!/bin/bash
# Memory Dedup - 长期记忆自动去重
# 用法：bash scripts/memory-dedup.sh
# 功能：检测并清理重复内容、无意义日常、重复任务进度

WORKSPACE_DIR="$HOME/.openclaw/workspace"
MEMORY_FILE="$WORKSPACE_DIR/MEMORY.md"
BACKUP_FILE="$WORKSPACE_DIR/MEMORY.md.backup.$(date +%Y%m%d-%H%M%S)"

echo "🔍 检查长期记忆重复..."

# 检查 MEMORY.md 是否存在
if [ ! -f "$MEMORY_FILE" ]; then
    echo "⚠️  MEMORY.md 不存在，跳过"
    exit 0
fi

# 创建备份
cp "$MEMORY_FILE" "$BACKUP_FILE"
echo "✅ 备份：$BACKUP_FILE"

TEMP_FILE=$(mktemp)

echo "📊 分析记忆内容..."

# 高级去重：使用 awk 检测并清理
# 1. 重复的上下文
# 2. 毫无意义的日常
# 3. 重复的任务进度提示
echo "🔄 执行智能去重..."

awk '
BEGIN { 
    RS = "\n\n"  # 段落分隔符
    ORS = "\n\n"
    skip_count = 0
}
{
    # 移除首尾空白
    gsub(/^[ \t]+|[ \t]+$/, "", $0)
    
    # 跳过空段落
    if (length($0) < 10) next
    
    # ❌ 跳过无意义日常
    if ($0 ~ /无事发生|毫无意义|无价值内容|NO_REPLY/) {
        skip_count++
        next
    }
    
    # ❌ 跳过重复的任务进度提示
    if ($0 ~ /任务进度|进度检查|待办事项.*检查/) {
        skip_count++
        next
    }
    
    # 生成简化的 key（用于去重）
    key = $0
    gsub(/[ \t]+/, " ", key)  # 多个空格变一个
    gsub(/^[^:]*: /, "", key)  # 移除前缀
    
    # ❌ 跳过重复的上下文
    if (key in seen) {
        skip_count++
        next
    }
    
    # 保留唯一内容
    seen[key] = 1
    print $0
}
END {
    print "" > "/dev/stderr"
    printf "📊 去重统计：删除 %d 个重复/无效段落\n", skip_count > "/dev/stderr"
}
' "$MEMORY_FILE" > "$TEMP_FILE"

# 检查去重后的文件
if [ -s "$TEMP_FILE" ]; then
    # 恢复文件结构（添加标题等）
    {
        echo "# MEMORY.md - 长期记忆"
        echo ""
        echo "> 精选知识与模式"
        echo ""
        echo "---"
        echo ""
        cat "$TEMP_FILE"
    } > "$MEMORY_FILE"
    
    echo "✅ 去重完成!"
    echo "📊 原始大小：$(wc -l < "$BACKUP_FILE") 行"
    echo "📊 去重后：$(wc -l < "$MEMORY_FILE") 行"
    echo "💾 备份位置：$BACKUP_FILE"
else
    echo "⚠️  去重后文件为空，恢复备份"
    cp "$BACKUP_FILE" "$MEMORY_FILE"
fi

# 清理临时文件
rm -f "$TEMP_FILE"
