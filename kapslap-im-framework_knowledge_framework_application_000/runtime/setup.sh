#!/bin/bash
set -e

# Ensure tools script is executable
chmod +x /workspace/tools/grep_helper.sh 2>/dev/null || true

# Verify references are in place
echo "=== Reference files ==="
ls -la /workspace/references/

# Quick sanity check on graph
echo ""
echo "=== Graph line count ==="
wc -l /workspace/references/graph.jsonl

echo ""
echo "=== Entity type distribution (put ops only) ==="
python3 -c "
import json
from collections import Counter
c = Counter()
for line in open('/workspace/references/graph.jsonl'):
    d = json.loads(line)
    if d.get('op') == 'put' and 'entity' in d:
        c[d['entity']['type']] += 1
for k, v in sorted(c.items()):
    print(f'  {k}: {v}')
"

echo ""
echo "Setup complete. Workspace ready."