#!/usr/bin/env bash
set -e

# Install the mock akshare package so `import akshare` resolves to our deterministic mock
pip install -e /workspace/mock_akshare_pkg/ -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

# Verify mock installation
python -c "import akshare as ak; df = ak.stock_zh_a_hist('000001', period='daily', start_date='20240101', end_date='20240630', adjust='qfq'); print(f'Mock akshare OK: {len(df)} rows for 000001')"

echo "=== Setup complete. Mock akshare installed. ==="
echo "Workspace contents:"
ls /workspace/