#!/bin/bash
set -e

echo "=== Setting up NDA task sandbox ==="

# Verify open-agreements CLI is installed
if command -v open-agreements >/dev/null 2>&1; then
    echo "✓ open-agreements CLI detected"
    open-agreements --version || true
else
    echo "✗ open-agreements CLI NOT found - installing..."
    npm install -g open-agreements --registry https://registry.npmjs.org
fi

# Verify Node.js version
echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"

# Verify python3-docx is available for evaluation
python3 -c "import docx; print('✓ python-docx available')" || pip3 install python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple

# Set permissions on workspace
chmod -R 755 /workspace

# Clean any leftover /tmp/oa-values.json from previous runs
rm -f /tmp/oa-values.json

echo "=== Sandbox setup complete ==="
echo "Workspace contents:"
find /workspace -type f | sort