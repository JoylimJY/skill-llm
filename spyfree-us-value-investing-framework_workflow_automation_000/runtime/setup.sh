#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/evaluate_company.py

# Ensure .state directory exists with proper permissions
mkdir -p /workspace/.state

echo "Setup complete. Workspace ready."
echo "Key files:"
echo "  SKILL.md                          — framework documentation"
echo "  references/input-template.json   — input schema"
echo "  scripts/evaluate_company.py       — deterministic evaluator"
echo "  data/raw/filings/                 — three company data files"
echo "  docs/committee/screening_brief.txt— task context"