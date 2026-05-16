#!/bin/bash
set -e

echo "=== Setup: PureRoot Botanicals SEO Memory Workspace ==="

# Verify workspace structure was created
if [ ! -d "/workspace/memory" ]; then
    echo "ERROR: Workspace not initialized. Running gen_inputs_script..."
    exit 1
fi

echo "Directory structure:"
find /workspace/memory -type d | sort

echo ""
echo "File inventory:"
find /workspace/memory -type f | sort

echo ""
echo "Hot-cache.md line count:"
wc -l /workspace/memory/hot-cache.md

echo ""
echo "Files older than 90 days:"
find /workspace/memory -name "*.md" -not -path "*/archive/*" | while read f; do
    age=$(( ($(date +%s) - $(stat -c %Y "$f")) / 86400 ))
    if [ "$age" -ge 90 ]; then
        echo "  $f ($age days old)"
    fi
done

echo ""
echo "=== Setup complete ==="