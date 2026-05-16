#!/bin/bash
set -e

echo "=== Setting up interview-assistant environment ==="

# Verify interview-assistant is installed
if command -v interview-assistant &> /dev/null; then
    echo "✅ interview-assistant CLI found: $(which interview-assistant)"
    interview-assistant --version 2>/dev/null || echo "(no --version flag)"
else
    echo "❌ interview-assistant not found, attempting reinstall..."
    npm install -g interview-assistant --registry https://registry.npmmirror.com
fi

# Ensure workspace directory exists and has correct permissions
mkdir -p /workspace/hr_department/candidates/shortlisted
chmod -R 755 /workspace

echo "=== Setup complete ==="
echo "Workspace contents:"
ls -la /workspace/