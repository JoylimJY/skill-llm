#!/bin/bash
set -e

echo "=== Setting up habit-tracker environment ==="

# Clone habit-tracker if not already present
if [ ! -d "/workspace/habit-tracker" ]; then
    git clone --depth 1 https://github.com/tianhm/habits-tracker.git /workspace/habit-tracker || true
fi

# If clone failed, create a minimal stub so the rest of setup doesn't break
if [ ! -d "/workspace/habit-tracker" ]; then
    mkdir -p /workspace/habit-tracker
    echo '{"name":"habits-tracker","version":"1.0.0"}' > /workspace/habit-tracker/package.json
fi

cd /workspace/habit-tracker

# Install dependencies if package.json exists
if [ -f "package.json" ]; then
    npm install 2>/dev/null || true
fi

# Ensure the CLI script is executable
if [ -f "scripts/habit-cli.js" ]; then
    chmod +x scripts/habit-cli.js
    echo "habit-cli.js found and made executable."
else
    echo "WARNING: scripts/habit-cli.js not found. Checking structure..."
    find /workspace/habit-tracker -name "*.js" | head -20
fi

# Create the config directory
mkdir -p ~/.config/habit-tracker

# Verify node works
node --version
echo "=== Setup complete ==="