#!/bin/bash
set -e

echo "[setup] Verifying Node.js installation..."
node --version

echo "[setup] Verifying meihua script exists and is executable..."
ls -la /root/clawd/skills/meihua-yishu/scripts/meihua.js
chmod +x /root/clawd/skills/meihua-yishu/scripts/meihua.js

echo "[setup] Quick smoke test of meihua script..."
node /root/clawd/skills/meihua-yishu/scripts/meihua.js "2024-01-01 09:15"

echo "[setup] SKILL.md accessible at /root/clawd/skills/meihua-yishu/SKILL.md"
ls -la /root/clawd/skills/meihua-yishu/SKILL.md

echo "[setup] Workspace contents:"
find /workspace -type f | sort

echo "[setup] Setup complete."