#!/bin/bash
set -e

# Ensure career directory exists and has correct permissions
mkdir -p /root/career
chmod 755 /root/career

# Ensure workspace is accessible
chmod -R 755 /workspace

# The session notes and distractor files are already in place from gen_inputs_script
echo "Setup complete. Career skill auxiliary files:"
ls -la /root/career/

echo "Workspace contents:"
find /workspace -type f | sort