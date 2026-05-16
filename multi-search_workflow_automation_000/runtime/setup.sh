#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying workspace structure..."
tree /workspace -L 3 2>/dev/null || find /workspace -maxdepth 3 -type f | head -40

echo "Setup complete."