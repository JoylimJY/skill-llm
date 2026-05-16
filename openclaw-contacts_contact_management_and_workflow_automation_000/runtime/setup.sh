#!/bin/bash
set -e

# Make all contact scripts executable
chmod +x /workspace/skills/contacts/scripts/list.sh
chmod +x /workspace/skills/contacts/scripts/search.sh
chmod +x /workspace/skills/contacts/scripts/get.sh

# Add the contacts scripts directory to PATH system-wide
echo 'export PATH="/workspace/skills/contacts/scripts:$PATH"' >> /etc/bash.bashrc
export PATH="/workspace/skills/contacts/scripts:$PATH"

echo "Setup complete. Contact scripts are executable and PATH is configured."
echo "Scripts available: list.sh, search.sh, get.sh"