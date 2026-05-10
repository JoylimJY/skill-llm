#!/bin/bash
# Continue on errors so all skills get attempted

# 默认值
NUM_INSTANCES=2
INPUT_DIR=""
TARGET_DIR=""

# 解析命令行参数
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -i|--input-dir)
            INPUT_DIR="$2"
            shift 2
            ;;
        -o|--output-dir)
            TARGET_DIR="$2"
            shift 2
            ;;
        -n|--num)
            NUM_INSTANCES="$2"
            shift 2
            ;;
        -h|--help)
            echo "用法: $0 -i <输入目录> -o <输出目录> [-n <生成数量>]"
            echo "示例: $0 -i 'openclaw_skills/Devops And Cloud' -o 'instance/instances_openclaw_skills_Devops And Cloud' -n 6"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 -h 或 --help 查看用法。"
            exit 1
            ;;
    esac
done

# 校验必填参数
if [ -z "$INPUT_DIR" ] || [ -z "$TARGET_DIR" ]; then
    echo "错误: 必须提供 --input-dir 和 --output-dir 参数。"
    echo "使用 -h 或 --help 查看用法。"
    exit 1
fi

total=0; success=0; failed=0

# 确保输出目录存在，避免 ls 报错
mkdir -p "$TARGET_DIR"

# 遍历输入目录下的所有子目录
for skill_dir in "$INPUT_DIR"/*/; do
    # 如果目录为空，通配符可能不展开，这里加一个防御性判断
    [ -d "$skill_dir" ] || continue
    
    skill=$(basename "$skill_dir")
    total=$((total+1))
    
    # 在正确的目录下检查是否已经有指定数量的实例
    existing=$(ls -d "$TARGET_DIR"/${skill}_* 2>/dev/null | wc -l)
    
    if [ "$existing" -ge "$NUM_INSTANCES" ]; then
        echo "SKIP (already have $existing instances): $skill"
        success=$((success+1))
        continue
    fi
    
    echo "=== Synthesizing: $skill ($NUM_INSTANCES instances) ==="
    # 使用传入的参数执行 python 脚本
    if uv run python -m src.run synthesize --skill-dir "$skill_dir" --num "$NUM_INSTANCES" --output-dir "$TARGET_DIR"; then
        success=$((success+1))
    else
        echo "FAILED: $skill"
        failed=$((failed+1))
    fi
done

echo "=== Synthesis complete: $success/$total skills succeeded, $failed failed ==="

# 统计最终生成的结果
echo "Total generated directories in $TARGET_DIR:"
ls -l "$TARGET_DIR" | grep ^d | wc -l