#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/quick_check.py 2>/dev/null || true
chmod +x /workspace/scripts/position_calculator.py 2>/dev/null || true

echo "Workspace ready."
echo "Candidate stocks file: /workspace/data/raw/candidate_stocks_today.csv"
echo "Agent should produce recommendation report as per the overnight trading strategy."