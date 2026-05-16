#!/bin/bash
set -e

# Ensure executable permissions
chmod -R 755 /workspace/tools/scripts/

# Verify key files exist
echo "Verifying workspace..."
test -f /workspace/data/incoming/complaints_batch.json && echo "OK: complaints_batch.json"
test -f /workspace/skill/SKILL.md && echo "OK: SKILL.md"
test -f /workspace/skill/references/classification-guide.md && echo "OK: classification-guide.md"
test -f /workspace/skill/references/response-templates.md && echo "OK: response-templates.md"
test -f /workspace/skill/configs/permissions_config.json && echo "OK: permissions_config.json"

echo "Setup complete. Workspace is ready."