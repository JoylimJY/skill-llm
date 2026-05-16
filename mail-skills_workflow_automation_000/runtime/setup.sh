#!/usr/bin/env bash
set -e

# Make the CLI executable
chmod +x /workspace/scripts/mail_cli.py

# Ensure tmp directory exists for counter files
mkdir -p /workspace/tmp

# Ensure reports directory exists
mkdir -p /workspace/reports

# Ensure logs directory exists
mkdir -p /workspace/logs

# Create an empty audit log file so appends work immediately
touch /workspace/logs/cli_audit.jsonl

echo "✓ Setup complete. mail_cli.py is ready."
echo "  Run: /workspace/scripts/mail_cli.py --help"