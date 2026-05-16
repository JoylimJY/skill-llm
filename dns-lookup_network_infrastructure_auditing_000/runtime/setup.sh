#!/bin/bash
# No mock servers needed — real public DNS is used.
# Ensure dig is available and working.
echo "[setup] Verifying dig availability..."
which dig && dig --version 2>&1 | head -1 || echo "WARNING: dig not found"
echo "[setup] Setup complete."