#!/usr/bin/env bash
set -e

# Ensure directories exist and permissions are correct
mkdir -p /root/.openclaw/workspace/novel
mkdir -p /root/.openclaw/workspace/notes
mkdir -p /root/.openclaw/config
mkdir -p /root/Desktop

# Verify key files are in place
echo "=== Setup: Verifying workspace ==="
ls /root/.openclaw/workspace/novel/
ls /root/Desktop/

echo "=== Setup complete ==="