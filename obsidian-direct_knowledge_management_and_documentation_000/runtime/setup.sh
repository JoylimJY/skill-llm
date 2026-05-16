#!/bin/bash
set -e

export OBSIDIAN_VAULT=/home/ruslan/webdav/data/ruslain

# Install python-yaml if not present
pip install PyYAML python-frontmatter -i https://pypi.tuna.tsinghua.edu.cn/simple -q 2>/dev/null || true

# Make sure scripts are executable
chmod +x /home/ruslan/.openclaw/workspace/skills/obsidian/scripts/obsidian_cli.py
chmod +x /home/ruslan/.openclaw/workspace/skills/obsidian/scripts/obsidian_search.py

# Verify vault exists
if [ ! -d "$OBSIDIAN_VAULT" ]; then
    echo "ERROR: Vault not found at $OBSIDIAN_VAULT"
    exit 1
fi

# Generate the vault content
python3 /workspace/gen_inputs.py 2>/dev/null || true

echo "Setup complete. Vault at: $OBSIDIAN_VAULT"
echo "Available notes:"
find "$OBSIDIAN_VAULT" -name "*.md" ! -path "*/.obsidian/*" | sort