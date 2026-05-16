#!/usr/bin/env bash
set -e

# Ensure the notes directories exist and are owned by node
mkdir -p /home/node/.openclaw/workspace/notes/ideas
mkdir -p /home/node/.openclaw/workspace/notes/projects
mkdir -p /home/node/.openclaw/workspace/notes/daily
mkdir -p /home/node/.openclaw/workspace/notes/misc

chown -R node:node /home/node/.openclaw 2>/dev/null || true

echo "Setup complete. Notes workspace ready."