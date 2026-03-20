#!/bin/bash
total=0; success=0; failed=0
for inst in instances/*/; do
    inst=${inst%/}
    total=$((total+1))
    # Skip already-built instances
    status=$(python3 -c "import json; d=json.load(open('$inst/task.json')); print(d.get('build_status',''))" 2>/dev/null || echo "")
    if [ "$status" = "success" ]; then
        echo "SKIP (already built): $inst"
        success=$((success+1))
        continue
    fi
    echo "=== Building: $(basename $inst) ==="
    if uv run python -m src.run build --instance "$inst"; then
        success=$((success+1))
    else
        failed=$((failed+1))
    fi
done
echo "=== Build complete: $success/$total success, $failed failed ==="
