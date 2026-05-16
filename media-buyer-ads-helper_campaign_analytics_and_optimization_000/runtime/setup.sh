#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying input files exist..."
for f in \
  "/workspace/accounts/meta/campaigns/account_structure_snapshot.json" \
  "/workspace/accounts/meta/campaigns/bidding_config.json" \
  "/workspace/accounts/meta/campaigns/budget_allocation_snapshot.json" \
  "/workspace/accounts/meta/campaigns/recent_performance_series.json" \
  "/workspace/accounts/meta/campaigns/test_history.json" \
  "/workspace/accounts/meta/campaigns/alert_thresholds.json"; do
  if [ -f "$f" ]; then
    echo "  OK: $f"
  else
    echo "  MISSING: $f"
    exit 1
  fi
done

echo "Setup complete. Workspace ready for agent."