#!/bin/bash
set -e

# Ensure the workspace has correct permissions
chmod -R 755 /workspace

# Attempt to install Poppins and Lora fonts if available via apt (may not be, so just try)
# These are not guaranteed; the skill has fallback logic for Arial/Georgia
apt-get install -y fonts-open-sans 2>/dev/null || true

# Refresh font cache
fc-cache -f -v 2>/dev/null || true

echo "Setup complete."