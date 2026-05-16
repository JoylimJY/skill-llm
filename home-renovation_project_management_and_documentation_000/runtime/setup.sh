#!/bin/bash
set -e

# Ensure the home-renovation skill directory root exists (as specified in SKILL.md)
mkdir -p ~/home-renovation/projects
mkdir -p ~/home-renovation/archive

# Set correct permissions on workspace
chmod -R 755 /home/user/workspace

echo "Setup complete. ~/home-renovation/ structure initialized."
echo "Workspace contents:"
find /home/user/workspace -maxdepth 2 -type f | sort