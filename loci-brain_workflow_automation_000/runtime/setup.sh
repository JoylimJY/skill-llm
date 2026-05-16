#!/bin/bash
set -e

# Ensure root home exists and loci template is owned correctly
chown -R root:root /root/loci 2>/dev/null || true

# Make sure ~/.loci does NOT exist (clean state for the agent to bootstrap)
rm -rf /root/.loci

# Verify the briefing file exists
if [ ! -f /workspace/initial_briefing.md ]; then
    echo "ERROR: initial_briefing.md not found!"
    exit 1
fi

echo "Setup complete. Agent must:"
echo "  1. Detect ~/loci/plan.md exists with status: template"
echo "  2. Run First-Time Setup using briefing.md data"
echo "  3. Register brain path to ~/.loci/brain-path"
echo "  4. Distill all 5 items from the briefing into correct destinations"