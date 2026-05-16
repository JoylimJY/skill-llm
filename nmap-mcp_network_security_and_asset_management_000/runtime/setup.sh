#!/bin/bash
set -e

echo "[setup] Verifying nmap capability..."
getcap $(which nmap) || true

echo "[setup] Setting cap_net_raw on nmap binary..."
setcap cap_net_raw+ep $(which nmap) || true
getcap $(which nmap)

echo "[setup] Installing python dependencies if needed..."
pip3 install fastmcp python-nmap pyyaml -q -i https://pypi.tuna.tsinghua.edu.cn/simple || true

echo "[setup] Verifying nmap-mcp directory..."
ls /workspace/nmap-mcp/

echo "[setup] Making server.py executable..."
chmod +x /workspace/nmap-mcp/server.py 2>/dev/null || true

echo "[setup] Setup complete."