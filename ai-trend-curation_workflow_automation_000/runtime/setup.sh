#!/bin/bash
set -e

chmod +x /usr/local/bin/xurl
chmod +x /usr/local/bin/openclaw
chmod +x /workspace/scripts/ai_trends.js

# Verify node works with the mock script
cd /workspace
node scripts/ai_trends.js search > /dev/null && echo "[setup] ai_trends.js search: OK"
node scripts/ai_trends.js check-recent > /dev/null && echo "[setup] ai_trends.js check-recent: OK"

echo "[setup] All mock binaries ready."
echo "[setup] Workspace ready for agent."