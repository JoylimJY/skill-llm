#!/bin/bash
set -e

echo "Setting up evaluation environment..."

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Setup complete. Agent should analyze /workspace/NSLG_raw_financial_data.json"
echo "and produce /workspace/NSLG_analysis_report.json"