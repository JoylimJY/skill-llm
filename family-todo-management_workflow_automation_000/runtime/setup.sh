#!/bin/bash
set -e

# Make todo.js executable
chmod +x /workspace/skills/family-todo/todo.js

# Make cron script executable
chmod +x /workspace/cron/daily.sh

# Verify Node.js is available
node --version
npm --version

echo "Setup complete. Workspace is ready."
echo "Key files:"
echo "  - /workspace/skills/family-todo/todo.js  (needs USERS configuration)"
echo "  - /workspace/config/family_setup.json    (family setup specification)"
echo "  - /workspace/memory/                     (todo.json will be created here)"