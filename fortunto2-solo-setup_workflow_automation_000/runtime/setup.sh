#!/usr/bin/env bash
set -e

echo "=== DataFlux workspace setup ==="

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify key files exist
for f in /workspace/CLAUDE.md /workspace/docs/prd.md /workspace/pyproject.toml /workspace/Makefile /workspace/ruff.toml; do
    if [ -f "$f" ]; then
        echo "  ✓ $f"
    else
        echo "  ✗ MISSING: $f" && exit 1
    fi
done

# Confirm docs/workflow.md does NOT exist yet (the agent must create it)
if [ -f /workspace/docs/workflow.md ]; then
    echo "  ✗ docs/workflow.md already exists — test environment is corrupted" && exit 1
else
    echo "  ✓ docs/workflow.md absent (correct)"
fi

echo "=== Setup complete ==="