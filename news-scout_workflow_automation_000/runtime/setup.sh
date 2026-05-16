#!/bin/bash
set -e

# Make scout.py executable
chmod +x /workspace/news-scout/scripts/scout.py

# Verify the script works
echo "Verifying scout.py..."
python3 /workspace/news-scout/scripts/scout.py --category ai,investing > /tmp/scout_test.json
echo "Scout script produces $(python3 -c "import json; d=json.load(open('/tmp/scout_test.json')); print(d['total'])") items"

echo "Setup complete. Workspace ready."
ls -la /workspace/news-scout/scripts/