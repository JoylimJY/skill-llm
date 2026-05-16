#!/bin/bash
set -e

# Make all skill scripts executable
chmod +x /workspace/.openclaw/workspace/skills/open-memory-system/scripts/memory.py
chmod +x /workspace/.openclaw/workspace/skills/open-memory-system/scripts/distill_l2.py
chmod +x /workspace/.openclaw/workspace/skills/open-memory-system/scripts/auto-save-memory/run.sh

# Set MEMORY_DIR environment variable system-wide for the session
export MEMORY_DIR=/workspace/.openclaw/workspace/memory
echo "export MEMORY_DIR=/workspace/.openclaw/workspace/memory" >> /etc/bash.bashrc
echo "export MEMORY_DIR=/workspace/.openclaw/workspace/memory" >> /root/.bashrc

# Ensure the hooks directory for auto-save-memory deployment target exists
mkdir -p /workspace/.openclaw/hooks

# Verify the skill scripts are syntactically valid Python
python3 -c "import py_compile; py_compile.compile('/workspace/.openclaw/workspace/skills/open-memory-system/scripts/memory.py')"
python3 -c "import py_compile; py_compile.compile('/workspace/.openclaw/workspace/skills/open-memory-system/scripts/distill_l2.py')"

echo "[setup] Environment ready. MEMORY_DIR=$MEMORY_DIR"
echo "[setup] Skill scripts available at: /workspace/.openclaw/workspace/skills/open-memory-system/scripts/"