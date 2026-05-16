#!/usr/bin/env bash
set -e

# Ensure the copy_to_onedrive.py script is executable
chmod +x /root/.openclaw/skills/onedrive-integration/scripts/copy_to_onedrive.py
chmod +x /root/.openclaw/skills/onedrive-integration/scripts/onboard.sh

echo "Setup complete."
echo "Skill scripts:"
ls -la /root/.openclaw/skills/onedrive-integration/scripts/
echo "Fake OneDrive root:"
ls -la /workspace/FakeOneDrive/
echo "Source files to copy:"
find /workspace/CaseDocs /workspace/LegalTeam /workspace/archive -type f | sort