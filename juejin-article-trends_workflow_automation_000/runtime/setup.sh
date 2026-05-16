#!/bin/bash
set -e

# Make the juejin script executable
chmod +x /workspace/scripts/juejin.js

# Verify node is available and the script works
echo "Verifying juejin.js script..."
node /workspace/scripts/juejin.js categories > /dev/null 2>&1 && echo "categories command: OK" || echo "categories command: FAILED"
node /workspace/scripts/juejin.js articles 6809637769959178254 hot 5 > /dev/null 2>&1 && echo "articles command: OK" || echo "articles command: FAILED"

echo "Setup complete. Workspace ready."
ls -la /workspace/scripts/