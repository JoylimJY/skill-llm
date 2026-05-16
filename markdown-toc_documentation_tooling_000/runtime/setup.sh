#!/bin/bash
set -e

# Ensure the skill script is executable
chmod +x /root/.openclaw/skills/markdown-toc/markdown_toc.py

# Verify workspace was generated
if [ ! -f /workspace/docs/api/api_reference.md ]; then
    echo "ERROR: Primary input file not found!"
    exit 1
fi

echo "Setup complete. Workspace is ready."
echo "Skill location: /root/.openclaw/skills/markdown-toc/markdown_toc.py"