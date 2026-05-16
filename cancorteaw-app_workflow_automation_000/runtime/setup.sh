#!/usr/bin/env bash
set -euo pipefail

# Ensure appctl is executable (belt-and-suspenders after gen_inputs_script)
chmod +x /home/patron/apps/_bin/appctl

# Put appctl on PATH for the patron user
echo 'export PATH="/home/patron/apps/_bin:$PATH"' >> /home/patron/.bashrc
export PATH="/home/patron/apps/_bin:$PATH"

# Kill the stale fake PID so `status oldapp` correctly reports STOPPED
# (the eval checks that the agent's new app shows RUNNING, not oldapp)
# PID 99999 almost certainly doesn't exist; this is a no-op safety measure.
kill 99999 2>/dev/null || true

# Configure git identity so commits inside appctl don't fail
git config --global user.email "patron@openclaw.local"
git config --global user.name "Patron"

# Pre-install create-expo-app and expo CLI in the global npm cache
# so the agent's `new` command doesn't time out on cold download.
npm install -g create-expo-app@latest expo-cli 2>/dev/null || true

echo "Setup complete."