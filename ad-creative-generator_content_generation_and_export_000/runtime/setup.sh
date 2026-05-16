#!/bin/bash
set -e

# Make generate.js executable
chmod +x /workspace/skills/ad-creative-generator/generate.js

# Verify Node.js is available
node --version

# Verify the skill files exist
ls -la /workspace/skills/ad-creative-generator/

echo "Setup complete."