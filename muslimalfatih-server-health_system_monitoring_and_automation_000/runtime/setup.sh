#!/bin/bash
set -e

# Ensure server-health.sh is executable
chmod +x /workspace/server-health.sh

# Verify the script runs correctly
echo "Verifying server-health.sh is functional..."
/workspace/server-health.sh --json > /tmp/health_test.json 2>&1
if [ $? -eq 0 ]; then
    echo "✅ server-health.sh --json: OK"
else
    echo "❌ server-health.sh --json: FAILED"
    cat /tmp/health_test.json
fi

/workspace/server-health.sh --alerts > /tmp/alerts_test.txt 2>&1
echo "✅ server-health.sh --alerts output: $(cat /tmp/alerts_test.txt | head -1)"

/workspace/server-health.sh --verbose > /tmp/verbose_test.txt 2>&1
if [ $? -eq 0 ]; then
    echo "✅ server-health.sh --verbose: OK"
else
    echo "❌ server-health.sh --verbose: FAILED"
fi

echo "Setup complete. Workspace ready for agent task."