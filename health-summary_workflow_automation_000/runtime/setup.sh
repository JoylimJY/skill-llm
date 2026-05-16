#!/bin/bash
set -e

chmod +x scripts/health_summary.js 2>/dev/null || true

# Verify node is available
node --version

# Verify the script runs correctly (smoke test)
node scripts/health_summary.js today --date=2026-03-15 > /dev/null 2>&1 && echo "health_summary.js smoke test passed" || echo "WARNING: smoke test failed"

echo "Setup complete."