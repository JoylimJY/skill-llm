#!/bin/bash
set -e

# Install the excel_parser skill from the workspace
cd /workspace

# The skill files should already exist in the workspace; ensure they're importable
# Create the excel_parser module if not already present from the skill installation
python -c "
import sys, os
# Check if excel_parser is importable
try:
    from excel_parser import ExcelParser, process_excel
    print('excel_parser already importable')
except ImportError:
    print('excel_parser not found, will need to be installed')
    sys.exit(1)
" 2>/dev/null || {
    # Install from PyPI as the skill docs indicate
    pip install excel-parser-skill -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || true
}

echo "Setup complete."