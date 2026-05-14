#!/usr/bin/env bash
set -e

echo "=== Setting up merge-check sandbox ==="

# Ensure all scripts are executable
chmod +x /workspace/skills/merge-check/scripts/merge-check.sh
chmod +x /workspace/scripts/lint-check.sh 2>/dev/null || true
chmod +x /workspace/scripts/deploy.sh 2>/dev/null || true

# Verify the mock script works
echo "=== Verifying mock script output ==="
OUTPUT=$(bash /workspace/skills/merge-check/scripts/merge-check.sh paycore-oss/payment-sdk#412)
DRAFT=$(echo "$OUTPUT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['pr']['draft'])")
echo "Mock script draft status: $DRAFT"
if [ "$DRAFT" != "True" ]; then
    echo "WARNING: Mock script draft field unexpected value: $DRAFT"
fi

echo "=== Sandbox ready ==="
echo "Task: Analyze PR paycore-oss/payment-sdk#412"
echo "Script location: /workspace/skills/merge-check/scripts/merge-check.sh"