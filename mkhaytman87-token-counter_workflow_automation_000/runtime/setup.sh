#!/usr/bin/env bash
set -e

# Make token-counter executable
chmod +x /workspace/openclaw_skills/token-counter/scripts/token-counter
chmod +x /workspace/openclaw_skills/skill-creator/scripts/quick_validate.py

# Verify environment variables are set correctly
echo "OPENCLAW_DATA_DIR   = $OPENCLAW_DATA_DIR"
echo "OPENCLAW_SKILLS_DIR = $OPENCLAW_SKILLS_DIR"
echo "OPENCLAW_WORKSPACE  = $OPENCLAW_WORKSPACE"

# Sanity check: sessions.json readable
python3 -c "
import json
from pathlib import Path
idx = Path('$OPENCLAW_DATA_DIR/agents/main/sessions/sessions.json')
data = json.loads(idx.read_text())
print(f'Sessions index loaded: {len(data[\"sessions\"])} sessions')
"

echo "Setup complete."