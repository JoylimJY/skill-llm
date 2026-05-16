#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key input files exist..."
test -f /workspace/system_cache/profiles/user_retail_007.json && echo "User profile: OK"
test -f /workspace/retail_project/logs/partial_session_20260225.json && echo "Partial session: OK"
test -f /workspace/TASK_BRIEF.md && echo "Task brief: OK"

echo "Setup complete."