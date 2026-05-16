#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Making run.py executable..."
chmod +x /workspace/skills/migration-runbook-generator/scripts/run.py

echo "[setup] Verifying Python and jinja2 availability..."
python3 -c "import jinja2; print('[setup] jinja2 OK:', jinja2.__version__)"

echo "[setup] Workspace tree (summary):"
find /workspace -type f | sort | head -40

echo "[setup] Done."