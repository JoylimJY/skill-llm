#!/bin/bash
set -e

# Ensure the self-improving directory has correct permissions
chmod -R 755 ~/self-improving/

# Confirm workspace files are readable
ls /workspace/session_log.txt > /dev/null
ls /workspace/.task_meta.json > /dev/null

echo "Setup complete. self-improving/ directory is ready."
echo "Contents of ~/self-improving/:"
find ~/self-improving/ -type f | sort