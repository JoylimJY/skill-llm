#!/bin/bash
set -e

# Make all scripts executable
chmod +x /workspace/skills/clawtip-weather/scripts/create_order.py
chmod +x /workspace/skills/clawtip-weather/scripts/weather_report.py
chmod +x /workspace/skills/clawtip/run.py
chmod +x /workspace/skills/clawtip/verif_server.py

# Start the credential verification server in the background
cd /workspace
python3 skills/clawtip/verif_server.py &
VERIF_PID=$!
echo "Credential verification server started with PID $VERIF_PID on 127.0.0.1:9988"

# Give it a moment to start
sleep 1

# Verify it's running
curl -s -X POST http://127.0.0.1:9988/register_credential \
     -H "Content-Type: application/json" \
     -d '{"credential":"HEALTH_CHECK","order_no":"TEST"}' \
     > /dev/null && echo "Verification server health check: OK" || echo "WARNING: Verification server may not be ready"

echo "Setup complete."