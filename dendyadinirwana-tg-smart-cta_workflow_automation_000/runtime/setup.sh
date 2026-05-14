#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key input files exist..."
ls /workspace/conversation_log.json
ls /workspace/TASK_BRIEF.md
ls /workspace/SKILL.md
ls /workspace/references/time_logic.md

echo "Setup complete. Workspace ready for agent."