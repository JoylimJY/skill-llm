#!/bin/bash
set -e

echo "Setting up Code Detective evaluation environment..."

chmod -R 755 /workspace

echo "Workspace contents:"
find /workspace -type f | sort

echo "Setup complete."