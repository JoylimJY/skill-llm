#!/bin/bash

if [ -z "$1" ]; then
    exit 1
fi

TARGET_DIR="$1"

if [ ! -d "$TARGET_DIR" ]; then
    exit 1
fi

total=0; success=0; failed=0

for inst in "$TARGET_DIR"/*/; do
    if [ ! -d "$inst" ]; then
        continue
    fi

    inst=${inst%/}
    total=$((total+1))
    
    status=$(python3 -c "import json; d=json.load(open('$inst/task.json')); print('EXISTS' if 'build_status' in d else '')" 2>/dev/null || echo "")
    
    if [ "$status" = "EXISTS" ]; then
        echo "SKIP (already has build_status): $inst"
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

