#!/bin/bash
set -e

echo "[setup] Installing neuralink-decoder skill from local package..."
pip install -e /workspace/neuralink_decoder_pkg/ -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

echo "[setup] Verifying installation..."
neuralink-decoder decode 2>/dev/null | head -5

echo "[setup] Setup complete."