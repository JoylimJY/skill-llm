#!/bin/bash
set -e

echo "=== Setting up Chinese Workdays sandbox ==="

# Ensure skill files are executable
chmod +x /workspace/workdays_cmd.py 2>/dev/null || true

# Verify skill is importable
cd /workspace
python3 -c "
import sys
sys.path.insert(0, '/workspace')
try:
    from chinese_workdays import ChineseWorkdays
    print('[OK] ChineseWorkdays importable')
except Exception as e:
    print(f'[WARN] Import issue: {e}')
"

# Verify data directory
ls /workspace/data/ && echo "[OK] data/ directory present"

# Show the broken yaml so agent can find it
echo "[INFO] Current 2027.yaml status (broken):"
python3 -c "
import yaml
with open('/workspace/data/2027.yaml') as f:
    print('File exists, size:', len(f.read()), 'bytes')
"

echo "=== Setup complete ==="