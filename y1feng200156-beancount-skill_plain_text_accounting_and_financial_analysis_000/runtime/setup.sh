#!/bin/bash
set -e

chmod +x /workspace/scripts/analyze_beancount.py

echo "Setup complete. Workspace ready for agent."
echo "Key files:"
echo "  /workspace/data/raw/transactions_2023.csv  - Raw transaction data"
echo "  /workspace/data/raw/context_notes.csv      - Account context"
echo "  /workspace/scripts/analyze_beancount.py    - Analysis script"
echo "  /workspace/references/                      - Reference documentation"