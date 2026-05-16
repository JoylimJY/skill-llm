#!/usr/bin/env bash
set -e

# Make all skill scripts executable
chmod +x /workspace/skills/obsidian-ontology-sync/scripts/sync.py
chmod +x /workspace/skills/obsidian-ontology-sync/scripts/init.py
chmod +x /workspace/skills/obsidian-ontology-sync/scripts/setup-cron.py
chmod +x /workspace/skills/obsidian-ontology-sync/scripts/debug.py
chmod +x /workspace/skills/obsidian-ontology-sync/scripts/query.py
chmod +x /workspace/skills/ontology/scripts/ontology.py

# Ensure /root/life/pkm source notes are in place (symlink vault into /root)
mkdir -p /root/life/pkm
cp -rn /workspace/root/life/pkm/. /root/life/pkm/ 2>/dev/null || true

# Ensure var/cron exists
mkdir -p /workspace/var/cron

echo "[setup] Environment ready."
echo "[setup] Vault: /root/life/pkm"
echo "[setup] Scripts: /workspace/skills/obsidian-ontology-sync/scripts/"