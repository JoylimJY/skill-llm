#!/usr/bin/env bash
set -e

# Install the mock akshare package so `import akshare` works
pip install -e /workspace/mock_packages/ -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

echo "Mock akshare installed successfully."
python -c "import akshare as ak; print('akshare import OK, version stub installed')"