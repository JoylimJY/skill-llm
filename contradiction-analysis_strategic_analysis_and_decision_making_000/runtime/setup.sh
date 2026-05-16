#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key input files exist..."
test -f /workspace/company/strategy/2024/ceo_analysis_request.txt && echo "✓ CEO request found"
test -f /workspace/company/finance/reports/runway_alert.txt && echo "✓ Finance data found"
test -f /workspace/company/ops/incidents/inc_2024_08_outage.md && echo "✓ Incident report found"
test -f /workspace/company/engineering/infra/tech_debt_tracker.json && echo "✓ Tech debt tracker found"
test -f /workspace/company/product/roadmap/q4_roadmap_draft.md && echo "✓ Product roadmap found"
test -f /workspace/company/sales/q2/pipeline_summary.csv && echo "✓ Sales pipeline found"
test -f /workspace/skills/contradiction-analysis/README.md && echo "✓ Skill reference found"

echo "Setup complete. Workspace ready for agent."