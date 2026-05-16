#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying SKILL.md exists..."
ls -la /workspace/SKILL.md

echo "Current workspace state:"
find /workspace/memory -type f 2>/dev/null || echo "(memory directory partially initialized)"

echo "Setup complete."