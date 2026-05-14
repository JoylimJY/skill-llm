#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

echo "=== Setting up NexaPay pitch deck sandbox ==="

# Verify Node.js and npm packages
echo "Node version: $(node --version)"
echo "npm version: $(npm --version)"

# Verify pptxgenjs is available globally
node -e "const p = require('pptxgenjs'); console.log('pptxgenjs OK');"
node -e "const r = require('react-icons/fa'); console.log('react-icons OK');"
node -e "const s = require('sharp'); console.log('sharp OK');"

# Verify Python packages
python3 -c "import pptx; print('python-pptx OK')"
python3 -c "import markitdown; print('markitdown OK')"

# Make scripts executable (the pre-existing skill scripts)
find "${WORKSPACE}/scripts" -name "*.py" -exec chmod +x {} \; 2>/dev/null || true

echo "=== Sandbox setup complete ==="
echo "Task data available at: ${WORKSPACE}/data/company_brief.json"