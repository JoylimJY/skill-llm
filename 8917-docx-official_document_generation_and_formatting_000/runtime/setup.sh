#!/bin/bash
set -e

chmod +x /workspace/scripts/md2docx.py

# Verify python-docx is available
python3 -c "import docx; print('[OK] python-docx available')"

# Verify soffice is available
soffice --version && echo "[OK] LibreOffice available" || echo "[WARN] soffice not found"

echo "[SETUP] Workspace ready."