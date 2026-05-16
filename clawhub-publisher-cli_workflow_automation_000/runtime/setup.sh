#!/bin/bash
set -e

echo "=== Setting up ClawHub Publisher CLI ==="

cd /opt/clawhub-publisher

# Ensure deps and build are complete
if [ ! -f "dist/index.js" ]; then
    echo "Building clawhub-publisher..."
    npm install
    npm run build
fi

echo "=== Verifying CLI is functional ==="
node dist/index.js --help || true

echo "=== Setup complete ==="
echo "CLI available at: node /opt/clawhub-publisher/dist/index.js"
echo "Broken skill at:  /workspace/projects/summarizer-skill"