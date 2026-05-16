#!/bin/bash
set -e

echo "Setting up workspace..."

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Workspace ready. Agent should generate /workspace/sales_dashboard.js"
echo "or place it anywhere findable via rglob."