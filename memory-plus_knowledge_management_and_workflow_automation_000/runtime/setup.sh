#!/bin/bash
set -e

SKILL_DIR="$HOME/.openclaw/workspace/skills/memory-workflow"
WORKSPACE="$HOME/.openclaw/workspace"

echo "=== Setting up Memory Workflow environment ==="

# Make memory_ops.py executable
chmod +x "$SKILL_DIR/memory_ops.py"
chmod +x "$SKILL_DIR/scripts/save_session.py"

# Verify Python can import the skill
cd "$SKILL_DIR"
python3 -c "
import sys
sys.path.insert(0, '.')
from scripts.config import DATA_DIR, MEMORIES_DIR, FTS5_DB, KG_DB
from scripts.fts5 import get_conn
from scripts.tools import MemorySearch, MemoryStore, MemoryDedup, MemoryList
print('All imports OK')
print(f'DATA_DIR: {DATA_DIR}')
print(f'MEMORIES_DIR: {MEMORIES_DIR}')
"

# Test the CLI works
python3 memory_ops.py list
echo "=== Setup complete ==="
echo "Workspace: $WORKSPACE"
echo "Raw notes: $WORKSPACE/raw_research_notes.txt"
echo ""
echo "Agent task: Store ML research notes, run dedup, search, save results to search_results.json"