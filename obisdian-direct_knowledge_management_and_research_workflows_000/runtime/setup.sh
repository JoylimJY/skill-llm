#!/bin/bash
set -e

# Make scripts executable
chmod +x /home/ruslan/.openclaw/workspace/skills/obsidian/scripts/obsidian_search.py
chmod +x /home/ruslan/.openclaw/workspace/skills/obsidian/scripts/obsidian_cli.py

# Set environment variable globally
export OBSIDIAN_VAULT=/home/ruslan/webdav/data/ruslain
echo "export OBSIDIAN_VAULT=/home/ruslan/webdav/data/ruslain" >> /etc/profile
echo "export OBSIDIAN_VAULT=/home/ruslan/webdav/data/ruslain" >> /root/.bashrc

# Verify vault structure
echo "=== Vault structure ==="
find /home/ruslan/webdav/data/ruslain -name "*.md" | head -20

# Verify scripts work
echo "=== Testing CLI scripts ==="
cd /home/ruslan/.openclaw/workspace/skills/obsidian/scripts
python3 obsidian_cli.py --vault /home/ruslan/webdav/data/ruslain --json folders
echo "=== Setup complete ==="