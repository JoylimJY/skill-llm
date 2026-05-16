#!/bin/bash
set -e

echo "=== Setting up memory-archiver sandbox ==="

# Ensure all scripts are executable
find /root/.openclaw/workspace/skills/memory-archiver/scripts/ -name "*.sh" -exec chmod +x {} \;

# Ensure workspace directories have correct permissions
chmod -R 755 /root/.openclaw/workspace/

# Create a helper that tells the agent what today's date is for the task
cat > /workspace/TASK_CONTEXT.txt << 'EOF'
TASK DATE: 2026-03-23
The system clock may differ. For all memory archival purposes, treat today as 2026-03-23.
EOF

echo "=== Setup complete ==="
echo "Workspace: /root/.openclaw/workspace/"
echo "Task input: /workspace/raw_session_notes.txt"
echo "Task date: 2026-03-23"