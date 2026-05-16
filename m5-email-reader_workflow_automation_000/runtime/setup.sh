#!/usr/bin/env bash
set -e

# Make the mock email_reader.py executable
chmod +x /workspace/scripts/email_reader.py

# Ensure the misleading root-level .email_config is NOT readable as a valid config
# (the real script only reads scripts/.email_config)
chmod 644 /workspace/.email_config

echo "Setup complete. Mock email reader is ready."
echo "Workspace contents:"
find /workspace -type f | sort