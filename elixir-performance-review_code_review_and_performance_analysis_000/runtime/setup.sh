#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Workspace ready. Directory structure:"
find /workspace -type f | sort