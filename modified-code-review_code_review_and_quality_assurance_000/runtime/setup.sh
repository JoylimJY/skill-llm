#!/bin/bash
set -e

cd /workspace/payment-service

# Verify git status looks correct
echo "=== Git Status ==="
git status

echo ""
echo "=== Staged Diff Preview ==="
git diff --cached --stat

echo ""
echo "Workspace ready for agent code review task."