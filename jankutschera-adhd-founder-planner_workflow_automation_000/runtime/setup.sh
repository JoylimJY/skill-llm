#!/bin/bash
set -e

echo "Setting up ADHD Daily Planner sandbox..."

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify prior day log exists
if [ -f "/workspace/.openclaw/skills/adhd-daily-planner/daily/2025-06-09.md" ]; then
    echo "Prior day log present: OK"
else
    echo "ERROR: Prior day log missing!"
    exit 1
fi

# Verify brain dump exists
if [ -f "/workspace/todays_brain_dump.txt" ]; then
    echo "Brain dump file present: OK"
else
    echo "ERROR: Brain dump missing!"
    exit 1
fi

echo "Sandbox ready."