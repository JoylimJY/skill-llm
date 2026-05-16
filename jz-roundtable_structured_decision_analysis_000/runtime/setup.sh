#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key input file exists..."
ls /workspace/trading/reports/investment_brief_nova.md

echo "Setup complete."