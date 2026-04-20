#!/bin/bash

# 1. 检查是否传入了参数
if [ -z "$1" ]; then
    echo "请传入目标文件夹名称"
    exit 1
fi

TARGET_DIR="$1"

# 2. 检查传入的文件夹是否存在
if [ ! -d "$TARGET_DIR" ]; then
    echo "找不到文件夹 '$TARGET_DIR'，请检查路径是否正确"
    exit 1
fi

total=0; success=0; failed=0

for inst in "$TARGET_DIR"/*/; do
    if [ ! -d "$inst" ]; then
        echo "文件夹为空，跳过。"
        continue
    fi

    inst=${inst%/}
    total=$((total+1))
    
    # Skip already-built instances
    status=$(python3 -c "import json; d=json.load(open('$inst/task.json')); print(d.get('build_status',''))" 2>/dev/null || echo "")
    if [ "$status" = "success" ]; then
        echo "SKIP (already built): $inst"
        success=$((success+1))
        continue
    fi
    
    echo "=== Building: $(basename "$inst") ==="
    
    if uv run python -m src.run build --instance "$inst"; then
        success=$((success+1))
    else
        failed=$((failed+1))
    fi
done

echo "=== Build complete: $success/$total success, $failed failed ==="