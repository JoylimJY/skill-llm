#!/bin/bash
set -e

chmod +x /workspace/scripts/health_score_calculator.py
chmod +x /workspace/scripts/churn_risk_analyzer.py
chmod +x /workspace/scripts/expansion_opportunity_scorer.py

echo "Setup complete. Workspace ready."
echo "Input file: /workspace/assets/hrtech_customers_q1_2026.json"
echo "Scripts available in: /workspace/scripts/"