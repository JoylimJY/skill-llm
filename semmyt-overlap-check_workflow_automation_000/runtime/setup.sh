#!/bin/bash
set -e

# Ensure the mock gh binary is executable
chmod +x /usr/local/bin/gh

# Ensure call log is clean
rm -f /workspace/.gh_call_log.jsonl

# Verify mock works
echo "Verifying mock gh binary..."
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "ERROR")
if [ "$REPO" = "openforge/dbmigrate" ]; then
    echo "✓ Mock gh binary working correctly (repo: $REPO)"
else
    echo "✗ Mock gh binary check failed (got: $REPO)"
    exit 1
fi

echo "Setup complete."