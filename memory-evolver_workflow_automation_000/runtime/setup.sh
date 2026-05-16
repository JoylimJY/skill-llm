#!/usr/bin/env bash
set -e

echo "=== Setting up Memory Evolver environment ==="

# Make the index.py executable
chmod +x /workspace/skills/memory-evolver/index.py

# Verify the skill scripts exist
for f in index.py diagnose.py knowledge_graph.py config.json SKILL.md; do
    if [ ! -f "/workspace/skills/memory-evolver/$f" ]; then
        echo "ERROR: Missing required skill file: $f"
        exit 1
    fi
done

echo "=== Setup complete ==="
echo "Workspace contents:"
tree /workspace 2>/dev/null || find /workspace -type f | sort