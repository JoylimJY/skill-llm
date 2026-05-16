#!/bin/bash
set -e

echo "Setting up workspace..."

# Make the calculate_lawsuit_fee.py script executable
chmod +x /workspace/scripts/calculate_lawsuit_fee.py

# Verify the key input files exist
echo "Verifying input files..."
test -f /workspace/input_contract.txt && echo "✓ input_contract.txt"
test -f /workspace/input_case_facts.txt && echo "✓ input_case_facts.txt"
test -f /workspace/scripts/calculate_lawsuit_fee.py && echo "✓ calculate_lawsuit_fee.py"
test -f /workspace/references/risk-patterns.md && echo "✓ risk-patterns.md"
test -f /workspace/references/calculation-formulas.md && echo "✓ calculation-formulas.md"
test -f /workspace/references/document-skeletons.md && echo "✓ document-skeletons.md"

echo "Setup complete. Agent task is ready."