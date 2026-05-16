#!/bin/bash
set -e

echo "Setting up memory-governor evaluation workspace..."

# Ensure the memory directory exists
mkdir -p /workspace/memory

# Make sure all skill reference files are readable
chmod -R 644 /workspace/skills/memory-governor/references/*.md
chmod 644 /workspace/skills/memory-governor/SKILL.md

echo "Setup complete."