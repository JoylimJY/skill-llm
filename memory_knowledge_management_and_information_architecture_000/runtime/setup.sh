#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Ensure ~/memory does NOT exist at the start (agent must create it)
rm -rf ~/memory

# Confirm workspace-level memory/ and MEMORY.md exist (the ones agent must NOT touch)
ls -la /workspace/MEMORY.md
ls -la /workspace/memory/

echo "Setup complete. ~/memory does not exist. Agent must create it."
echo "Workspace-level MEMORY.md and memory/ are in place and must not be modified."

# Record the original modification times of the protected files
stat /workspace/MEMORY.md > /tmp/original_memory_md_stat.txt
stat /workspace/memory/2026-01-15.md > /tmp/original_memory_daily_stat.txt

echo "Original stats recorded for tamper detection."