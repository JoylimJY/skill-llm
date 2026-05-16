#!/bin/bash
set -e

echo "=== Setting up mock AkShare environment ==="

# Find the real akshare package location and inject our mock
AKSHARE_PATH=$(python3 -c "import akshare; import os; print(os.path.dirname(akshare.__file__))" 2>/dev/null || echo "")

if [ -n "$AKSHARE_PATH" ]; then
    echo "Found akshare at: $AKSHARE_PATH"
    # Backup original __init__.py
    cp "$AKSHARE_PATH/__init__.py" "$AKSHARE_PATH/__init__.py.bak" 2>/dev/null || true
    # Overwrite the akshare __init__.py with our mock
    cp /workspace/mock_akshare_data/mock_akshare_module.py "$AKSHARE_PATH/__init__.py"
    echo "Mock akshare installed successfully."
else
    echo "WARNING: akshare not found via pip, trying alternative approach..."
    # Create a local akshare.py that will shadow the real one
    cp /workspace/mock_akshare_data/mock_akshare_module.py /workspace/akshare.py
    echo "Fallback: created /workspace/akshare.py"
fi

# Make sure the mock data directory is accessible
chmod -R 755 /workspace/mock_akshare_data/

echo "=== Setup complete ==="
echo "Mock data files:"
ls -la /workspace/mock_akshare_data/

echo ""
echo "Task: Generate semiconductor sector stock analysis report"
echo "Output required: sector_analysis_report.json in /workspace/project/reports/final/"