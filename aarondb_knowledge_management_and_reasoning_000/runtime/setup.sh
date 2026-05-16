#!/bin/bash
set -e

cd /workspace

# Ensure node_modules symlink is accessible from workspace
if [ ! -d "/workspace/node_modules" ]; then
    ln -s /node_modules /workspace/node_modules 2>/dev/null || true
fi

# Initialize a package.json so the agent can use ES modules or CommonJS
cat > /workspace/package.json << 'EOF'
{
  "name": "supply-chain-intelligence",
  "version": "1.0.0",
  "description": "Supply chain fact reasoning workspace",
  "type": "module",
  "dependencies": {
    "@criticalinsight/aarondb-edge": "*"
  }
}
EOF

# Copy node_modules if not already present in workspace
if [ ! -d "/workspace/node_modules/@criticalinsight" ]; then
    cp -r /node_modules /workspace/node_modules 2>/dev/null || true
fi

echo "Setup complete. Workspace ready."
echo "Node version: $(node --version)"
echo "npm packages available: $(ls /workspace/node_modules | head -5)"