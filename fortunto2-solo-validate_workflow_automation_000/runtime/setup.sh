#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/seed_db.sh
chmod +x /workspace/scripts/deploy.sh

# Verify key reference files are present
echo "Checking reference files..."
[ -f /workspace/references/manifest-checklist.md ] && echo "✓ manifest-checklist.md present" || echo "✗ manifest-checklist.md MISSING"
[ -f /workspace/references/stream-layers.md ] && echo "✓ stream-layers.md present" || echo "✗ stream-layers.md MISSING"
[ -f /workspace/docs/research.md ] && echo "✓ research.md present" || echo "✗ research.md MISSING"

echo "Workspace ready. Agent task can begin."