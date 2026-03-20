#!/bin/bash
set -e

echo "Setting up workspace for Tesla market analysis agent..."

# Ensure all Python scripts are executable
chmod +x *.py

# Create output directories
mkdir -p outputs
mkdir -p charts

# Verify required packages
echo "Verifying package installations..."
python3 -c "import anthropic, pandas, matplotlib, reportlab, textblob, yfinance, sklearn, nltk; print('All packages available')"

echo "Setup complete!"