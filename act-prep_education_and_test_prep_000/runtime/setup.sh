#!/usr/bin/env bash
set -e

# Ensure the act directory exists and permissions are correct
mkdir -p ~/act/sections ~/act/practice ~/act/vocab ~/act/formulas

# Make all existing files readable/writable
chmod -R 644 ~/act/ 2>/dev/null || true
chmod -R 755 ~/act/ 2>/dev/null || true

echo "Setup complete. ACT prep workspace is ready."