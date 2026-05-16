#!/usr/bin/env bash
set -euo pipefail

export WORKSPACE="${WORKSPACE:-/workspace}"

echo "[setup] Setting OPENCLAW_WORKSPACE to $WORKSPACE"
echo "export OPENCLAW_WORKSPACE=$WORKSPACE" >> /etc/environment
echo "export OPENCLAW_WORKSPACE=$WORKSPACE" >> /root/.bashrc
export OPENCLAW_WORKSPACE="$WORKSPACE"

# Make the proprietary script executable
chmod +x "$WORKSPACE/scripts/run_usage_report.py"

# Install Python dependencies
pip install -q \
    matplotlib pandas numpy pillow jinja2 pytz \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "[setup] OPENCLAW_WORKSPACE=$OPENCLAW_WORKSPACE"
echo "[setup] Verifying script..."
python3 "$WORKSPACE/scripts/run_usage_report.py" --mode text --period week --json | python3 -c "import sys,json; d=json.load(sys.stdin); print('[setup] Script OK, total_sessions=', d['stats']['total_sessions'])"
echo "[setup] Done."