#!/bin/bash
set -e

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"

echo "[setup] Making all skill scripts executable..."
chmod +x "$WORKSPACE_DIR/skills/niri-ipc/scripts/"*.py

echo "[setup] Starting mock Niri IPC server..."
export NIRI_SOCKET="/tmp/niri_mock.sock"

# Start the mock server in background
python3 "$WORKSPACE_DIR/skills/niri-ipc/scripts/mock_niri_server.py" &
MOCK_PID=$!
echo $MOCK_PID > /tmp/mock_niri_pid.txt

# Wait for socket to appear
for i in $(seq 1 20); do
    if [ -S "$NIRI_SOCKET" ]; then
        echo "[setup] Mock Niri socket ready at $NIRI_SOCKET"
        break
    fi
    sleep 0.2
done

if [ ! -S "$NIRI_SOCKET" ]; then
    echo "[setup] ERROR: Mock socket did not appear!" >&2
    exit 1
fi

# Persist NIRI_SOCKET for the agent's shell sessions
echo "export NIRI_SOCKET=/tmp/niri_mock.sock" >> /etc/environment
echo "export NIRI_SOCKET=/tmp/niri_mock.sock" >> /root/.bashrc
echo "export NIRI_SOCKET=/tmp/niri_mock.sock" >> /root/.profile

# Quick sanity check
RESULT=$(NIRI_SOCKET=/tmp/niri_mock.sock python3 "$WORKSPACE_DIR/skills/niri-ipc/scripts/niri.py" workspaces 2>&1)
echo "[setup] Sanity check - workspaces response: $RESULT"

echo "[setup] Done. Mock server PID: $MOCK_PID"