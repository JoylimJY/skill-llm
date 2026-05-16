#!/bin/bash
set -e

# Make the mock fetch script executable
chmod +x /workspace/skills/china-holidays/scripts/fetch_holidays.py

# Verify the workspace structure
echo "=== Workspace structure ==="
find /workspace/skills/china-holidays -type f | sort

echo "=== Verifying mock script runs ==="
cd /workspace/skills/china-holidays
python scripts/fetch_holidays.py --year 2026 | head -5

echo "=== Verifying stale 2025 cache content ==="
head -5 /workspace/skills/china-holidays/assets/2025.md

echo "Setup complete."