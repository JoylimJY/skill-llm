#!/bin/bash
set -e

# Ensure the neet data directory does NOT pre-exist (agent must create it)
rm -rf ~/neet

# Make workspace readable
chmod -R 755 /workspace

echo "Setup complete. ~/neet/ does not exist yet — agent must create it."