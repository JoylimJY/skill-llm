#!/bin/bash
set -e

echo "[setup] Setting script permissions..."
chmod +x /workspace/lottery-ssq/scripts/update_ssq_history.py
chmod +x /workspace/lottery-ssq/scripts/generate_ssq.py
chmod +x /workspace/lottery-ssq/scripts/backtest_ssq.py

echo "[setup] Verifying workspace structure..."
ls /workspace/lottery-ssq/
ls /workspace/lottery-ssq/scripts/
ls /workspace/lottery-ssq/data/

echo "[setup] Verifying history data..."
python3 -c "
import csv
with open('/workspace/lottery-ssq/data/ssq_history.csv') as f:
    rows = list(csv.DictReader(f))
print(f'History rows: {len(rows)}')
assert len(rows) >= 3400, 'Not enough history rows'
"

echo "[setup] Ready."