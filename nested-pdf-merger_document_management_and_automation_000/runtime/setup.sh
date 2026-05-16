#!/usr/bin/env bash
set -e

# Ensure the workspace directory has correct permissions
chmod -R 755 /workspace/filings

# Verify nestedpdfmerger is installed
nestedpdfmerger --version || python -m nestedpdfmerger --version

echo "Setup complete. Workspace ready."