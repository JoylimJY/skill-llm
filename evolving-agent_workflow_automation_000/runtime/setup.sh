#!/bin/bash
set -e

# Ensure the run.py script is executable
SKILL_SCRIPT="$HOME/.config/opencode/skills/evolving-agent/scripts/run.py"
if [ -f "$SKILL_SCRIPT" ]; then
    chmod +x "$SKILL_SCRIPT"
    echo "[setup] run.py is executable: $SKILL_SCRIPT"
fi

# Verify the skill directory structure exists
SKILLS_DIR="$HOME/.config/opencode/skills"
echo "[setup] Skill root: $SKILLS_DIR/evolving-agent"

# Verify Python can import click (needed by run.py)
python3 -c "import click; print('[setup] click available:', click.__version__)"

# Ensure .opencode dir exists in workspace (it was created by gen_inputs but double-check)
mkdir -p /home/agent/project/.opencode
echo "[setup] .opencode directory confirmed at /home/agent/project/.opencode"

# Print current state summary for debugging
echo "[setup] Current .opencode contents:"
ls -la /home/agent/project/.opencode/ 2>/dev/null || echo "(empty)"

echo "[setup] Knowledge base entries:"
cat "$SKILLS_DIR/evolving-agent/data/knowledge/entries.json" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  {len(d)} entries')" || echo "  (none or missing)"

echo "[setup] Setup complete. Agent workspace ready at /home/agent/project"