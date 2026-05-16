#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/prepare_call_payload.py
chmod +x /workspace/scripts/place_outbound_call.py
chmod +x /workspace/scripts/parse_call_result.py

# Ensure /tmp is writable (it should be, but make sure)
mkdir -p /tmp
chmod 1777 /tmp

echo "Setup complete. Scripts are executable."