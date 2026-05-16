#!/usr/bin/env bash
set -e

echo "=== Setting up Gougoubi submission sandbox ==="

# Ensure all scripts are executable
chmod +x /workspace/scripts/*.mjs

# Verify Node.js is available
node --version

# Quick smoke-test of the scripts
echo "--- Smoke-testing skills-derived script ---"
node /workspace/scripts/pbft-submit-results-from-skills-once.mjs --help

echo "--- Smoke-testing fixed-side script ---"
node /workspace/scripts/pbft-submit-all-condition-results.mjs --help

echo "=== Setup complete ==="