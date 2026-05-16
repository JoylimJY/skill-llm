#!/usr/bin/env bash
set -e

# Ensure search.sh is executable (already done in Dockerfile, but belt-and-suspenders)
chmod +x /root/.openclaw/workspace/skills/code-search/scripts/search.sh

# Run the gen_inputs_script to populate the workspace
python3 /gen_inputs_script.py

echo "Setup complete. Workspace ready at /workspace/legacybank"
echo "Skill available at: /root/.openclaw/workspace/skills/code-search/scripts/search.sh"

# Verify the skill's dependency check runs cleanly
bash /root/.openclaw/workspace/skills/code-search/scripts/search.sh check