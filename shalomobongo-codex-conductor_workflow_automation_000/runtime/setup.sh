#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/*.py

# Ensure Python can run all scripts directly
for f in /workspace/scripts/*.py; do
  sed -i '1s|^#!/usr/bin/env python3|#!/usr/bin/env python3|' "$f" || true
done

echo "[setup] Scripts are executable and ready."
echo "[setup] Workspace contents:"
ls /workspace/