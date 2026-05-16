#!/bin/bash
set -e

echo "=== Setting up workspace ==="

# Make legacy scripts non-executable to prevent accidental use
chmod -x /workspace/scripts/legacy/old_ltv_v1.py 2>/dev/null || true

# Verify key input files exist
for f in \
    "/workspace/data/raw_orders/paid_social_orders_2023.csv" \
    "/workspace/data/marketing/paid_social_cost_breakdown_2023.txt" \
    "/workspace/business_context_memo.txt"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: Missing required file: $f"
        exit 1
    fi
done

echo "=== Setup complete ==="