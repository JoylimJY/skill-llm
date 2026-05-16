#!/usr/bin/env bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/init_skill.py
chmod +x /workspace/scripts/validate_skill.py
chmod +x /workspace/scripts/package_skill.py

echo "Setup complete. Scripts are executable."
echo "Workspace layout:"
tree /workspace --dirsfirst -L 4 2>/dev/null || find /workspace -maxdepth 4 | sort