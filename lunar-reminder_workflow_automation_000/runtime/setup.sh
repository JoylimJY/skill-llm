#!/usr/bin/env bash
set -e

# Add mock openclaw to PATH
export PATH="/workspace/mock_bin:$PATH"
echo 'export PATH="/workspace/mock_bin:$PATH"' >> /etc/profile
echo 'export PATH="/workspace/mock_bin:$PATH"' >> /root/.bashrc
echo 'export PATH="/workspace/mock_bin:$PATH"' >> /root/.profile

# Install lunar-javascript in the skill directory
cd /workspace/skills/lunar-reminder
npm install lunar-javascript --registry https://registry.npmmirror.com --save 2>&1 | tail -5

# Verify node can import lunar-javascript from the skill directory
node -e "const {Lunar}=require('lunar-javascript');console.log('lunar-javascript OK');"
echo "Setup complete. lunar-javascript available at /workspace/skills/lunar-reminder/node_modules"

# Make sure openclaw is executable and in path
chmod +x /workspace/mock_bin/openclaw
ln -sf /workspace/mock_bin/openclaw /usr/local/bin/openclaw || true

echo "Mock openclaw installed at /usr/local/bin/openclaw"