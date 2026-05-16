#!/usr/bin/env bash
set -e

# Ensure the workspace has correct ownership (already consultant user)
WORKSPACE="/home/consultant/workspace"

# Make sure ~/memory does NOT pre-exist (clean slate)
rm -rf /home/consultant/memory

# Verify workspace structure
echo "[setup] Workspace ready at: $WORKSPACE"
echo "[setup] HOME memory dir absent: $([ ! -d /home/consultant/memory ] && echo YES || echo NO)"
echo "[setup] Trap MEMORY.md present: $([ -f $WORKSPACE/MEMORY.md ] && echo YES || echo NO)"
echo "[setup] Trap memory/ present: $([ -d $WORKSPACE/memory ] && echo YES || echo NO)"
echo "[setup] Archive stubs: $(ls $WORKSPACE/raw_data/old_project_archive/ | wc -l)"