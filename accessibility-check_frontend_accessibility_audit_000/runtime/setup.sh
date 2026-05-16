#!/bin/bash
set -e

# Ensure scripts are executable
chmod +x /workspace/scripts/build.sh 2>/dev/null || true
chmod +x /workspace/scripts/deploy.sh 2>/dev/null || true

# Create a minimal package.json so the workspace looks like a real project
cat > /workspace/package.json << 'EOF'
{
  "name": "patient-portal",
  "version": "1.0.0",
  "description": "Healthcare Patient Portal",
  "main": "src/index.js",
  "scripts": {
    "build": "webpack --config config/webpack.config.js",
    "test": "jest"
  },
  "devDependencies": {
    "webpack": "^5.0.0",
    "babel-loader": "^9.0.0",
    "jest": "^29.0.0"
  }
}
EOF

echo "Setup complete. Workspace ready at /workspace"