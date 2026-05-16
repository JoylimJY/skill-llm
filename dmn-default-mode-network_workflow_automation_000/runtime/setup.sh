#!/bin/bash
set -e

echo "=== DMN Sandbox Setup ==="

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify critical files exist
echo "--- Checking critical input files ---"
test -f /workspace/dmn-state.json && echo "OK: dmn-state.json" || echo "MISSING: dmn-state.json"
test -f /workspace/assets/user-config.md && echo "OK: user-config.md" || echo "MISSING: user-config.md"
test -f /workspace/output/2026-06-11/20260611_DMN_Synthesis_2345.md && echo "OK: previous Synthesis" || echo "MISSING: previous Synthesis"
test -f /workspace/memory/evolve/candidates.md && echo "OK: candidates.md" || echo "MISSING: candidates.md"

echo "=== Setup complete ==="