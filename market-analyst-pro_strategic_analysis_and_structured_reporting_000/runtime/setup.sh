#!/bin/bash
set -e

echo "=== Setting up evaluation environment ==="

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify key input files exist
if [ ! -f /workspace/market_research/candidate_markets_raw.json ]; then
    echo "ERROR: candidate_markets_raw.json not found!"
    exit 1
fi

if [ ! -f /workspace/market_research/business_context.json ]; then
    echo "ERROR: business_context.json not found!"
    exit 1
fi

echo "=== Input files verified ==="
echo "Candidate markets data:"
python3 -c "
import json
with open('/workspace/market_research/candidate_markets_raw.json') as f:
    data = json.load(f)
for m in data:
    print(f'  {m[\"market_id\"]}: {m[\"country\"]} ({m[\"region\"]}) - Drive: {m[\"drive_side\"]} - Tariff: {m[\"ev_hybrid_import_tariff_pct\"]}%')
"

echo "=== Setup complete. Agent may begin. ==="