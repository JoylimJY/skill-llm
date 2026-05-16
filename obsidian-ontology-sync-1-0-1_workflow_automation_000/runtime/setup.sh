#!/usr/bin/env bash
set -euo pipefail

# Make all skill scripts executable
chmod +x /workspace/skills/obsidian-ontology-sync/scripts/sync.py
chmod +x /workspace/skills/obsidian-ontology-sync/scripts/init.py
chmod +x /workspace/skills/obsidian-ontology-sync/scripts/setup-cron.py
chmod +x /workspace/skills/obsidian-ontology-sync/scripts/query.py
chmod +x /workspace/skills/obsidian-ontology-sync/scripts/debug.py

# Ensure /root/life symlink exists pointing to the vault location in workspace
mkdir -p /root/life
if [ ! -e /root/life/pkm ]; then
    ln -s /workspace/life/pkm /root/life/pkm
fi

# Ensure cron is available (install if missing, silently)
which crontab >/dev/null 2>&1 || apt-get install -y -q cron >/dev/null 2>&1 || true

echo "Setup complete. Vault is at /root/life/pkm"
echo "Skill scripts are at /workspace/skills/obsidian-ontology-sync/scripts/"
echo ""
echo "Workspace structure:"
find /workspace/life/pkm -type f -name "*.md" | head -20
echo "..."