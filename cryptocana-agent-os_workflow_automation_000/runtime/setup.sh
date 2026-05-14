#!/bin/bash
set -e

cd /workspace

# Install agent-os properly
npm install agent-os --save 2>&1 | tail -5

# Make scripts executable
chmod +x warehouse-project/scripts/migrate.sh

# Verify agent-os installed
node -e "const { AgentOS } = require('agent-os'); console.log('agent-os loaded OK');" 2>&1

echo "Setup complete. agent-os is ready."