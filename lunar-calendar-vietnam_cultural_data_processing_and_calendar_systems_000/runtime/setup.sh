#!/bin/bash
set -e

# Make the calculator script executable
chmod +x /workspace/lunar-calendar-vietnam/scripts/amlich_calculator.js

# Verify Node.js is available
echo "Node version: $(node --version)"

# Quick sanity check that the script runs
cd /workspace/lunar-calendar-vietnam
TEST_OUTPUT=$(node scripts/amlich_calculator.js --solar "2025-01-01" 2>&1)
if echo "$TEST_OUTPUT" | grep -q '"lunar"'; then
    echo "amlich_calculator.js sanity check: PASSED"
else
    echo "amlich_calculator.js sanity check: FAILED"
    echo "Output was: $TEST_OUTPUT"
fi

echo "Setup complete."