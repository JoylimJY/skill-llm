#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/validate_json.sh 2>/dev/null || true

# Verify the template exists
if [ -f /workspace/templates/default.json ]; then
    echo "[OK] Template file found: /workspace/templates/default.json"
    cat /workspace/templates/default.json
else
    echo "[ERROR] Template file missing!"
    exit 1
fi

# Verify the conversation log exists
if [ -f /workspace/conversation_log.json ]; then
    echo "[OK] Conversation log found."
else
    echo "[ERROR] Conversation log missing!"
    exit 1
fi

echo "[SETUP COMPLETE] Workspace ready for agent."