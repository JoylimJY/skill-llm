#!/usr/bin/env bash
set -euo pipefail

echo "Setting up expense-tracker skill environment..."

# Make all scripts executable
chmod +x /workspace/skills/expense-tracker/scripts/add-expense.sh
chmod +x /workspace/skills/expense-tracker/scripts/query.sh
chmod +x /workspace/skills/expense-tracker/scripts/budget-check.sh

# Ensure ledger exists and is writable
touch /workspace/skills/expense-tracker/expenses/ledger.json
chmod 644 /workspace/skills/expense-tracker/expenses/ledger.json

# All script operations assume working directory is /workspace
cd /workspace

echo "Setup complete. Scripts are ready."
echo "Ledger path: /workspace/skills/expense-tracker/expenses/ledger.json"