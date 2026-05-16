#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/startup-read.js 2>/dev/null || true
chmod +x /workspace/scripts/weekly-archive.js 2>/dev/null || true
chmod +x /workspace/scripts/monthly-archive.js 2>/dev/null || true

# Ensure workspace permissions are correct
chown -R root:root /workspace
chmod -R 755 /workspace

echo "Setup complete. Workspace is ready."
echo "Today's date: $(date +%Y-%m-%d)"