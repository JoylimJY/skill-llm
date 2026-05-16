#!/bin/bash
set -e

# Ensure proper ownership and permissions
chown -R researcher:researcher /home/researcher/
chmod -R 755 /home/researcher/Downloads/

# Create the standard research base directory hint (just the parent, not the specific task folder)
mkdir -p /home/researcher/Downloads/research/
chown -R researcher:researcher /home/researcher/Downloads/research/

echo "Setup complete. Workspace ready for researcher user."