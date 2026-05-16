#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Verifying cashu-emoji installation..."
node /opt/cashu-emoji/bin/cashu-emoji.js --version 2>/dev/null || true
node /opt/cashu-emoji/bin/cashu-emoji.js --help 2>/dev/null || true

echo "[setup] Verifying workspace files..."
ls /workspace/marketplace/payments/pending/

echo "[setup] Setup complete."