#!/usr/bin/env bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/decode_serial.py

# Verify the decoder script works
echo "=== Verifying decoder script ==="
python3 /workspace/scripts/decode_serial.py C02JH7GJDKQ1 | python3 -c "import sys,json; d=json.load(sys.stdin); print('Decoder OK:', d.get('format'))"

echo "=== Workspace ready ==="
ls -la /workspace/