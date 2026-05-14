#!/bin/bash
set -e

# Add mock sui to PATH (prepend so it takes priority over any system sui)
echo 'export PATH="/workspace/bin:$PATH"' >> /etc/environment
export PATH="/workspace/bin:$PATH"

# Make all skill scripts executable
chmod +x /workspace/skills/sui-coverage/analyze_source.py
chmod +x /workspace/skills/sui-coverage/analyze.py
chmod +x /workspace/skills/sui-coverage/parse_bytecode.py
chmod +x /workspace/bin/sui

# Verify mock sui works
/workspace/bin/sui --version

# Set up a symlink so `sui` is on PATH for all shells
ln -sf /workspace/bin/sui /usr/local/bin/sui

# Verify
sui --version

echo "Setup complete. Workspace ready."
echo "Package path: /workspace/vault_package"
echo "Skills path: /workspace/skills/sui-coverage"