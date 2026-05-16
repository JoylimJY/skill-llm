#!/usr/bin/env bash
set -e

echo "[setup] Fixing permissions on skill scripts..."
chmod +x ~/.openclaw/workspace-pm/skills/community-data-process/run.py

echo "[setup] Verifying Downloads symlink..."
ls -la ~/Downloads/ | head -20

echo "[setup] Verifying file mtimes..."
python3 -c "
import os
from pathlib import Path
from datetime import datetime
dl = Path.home() / 'Downloads'
files = sorted(dl.glob('客户群导出*.xlsx'), key=lambda p: p.stat().st_mtime)
for f in files:
    mt = datetime.fromtimestamp(f.stat().st_mtime)
    print(f'  {f.name}: mtime={mt}')
"

echo "[setup] Setup complete."