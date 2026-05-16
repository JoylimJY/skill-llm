#!/bin/bash
set -e

echo "Setting up workspace..."
chmod -R 755 /workspace

# Make sure all paths are accessible
ls /workspace/research_institute/knowledge_base/raw/knowledge_dump.json
ls /workspace/research_institute/config/drafts/broken_config.json

echo "Workspace setup complete."
echo "Agent can begin work."