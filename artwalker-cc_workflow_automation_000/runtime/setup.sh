#!/bin/bash
set -e

# Ensure scripts directory exists and cc.sh is executable
chmod +x /workspace/scripts/cc.sh

# Reset the projects call counter so tests are deterministic
rm -f /tmp/cc_projects_calls

# Verify the mock script works
echo "Verifying mock cc.sh..."
# Test SETUP_NEEDED flow
OUTPUT=$(bash /workspace/scripts/cc.sh projects 2>&1); CODE=$?
if [ "$CODE" -eq 100 ] && [ "$OUTPUT" = "SETUP_NEEDED" ]; then
    echo "✓ SETUP_NEEDED (exit 100) works correctly"
else
    echo "✗ SETUP_NEEDED check failed: output='$OUTPUT' code=$CODE"
fi

# Test second call returns project list
OUTPUT=$(bash /workspace/scripts/cc.sh projects 2>&1); CODE=$?
if [ "$CODE" -eq 0 ]; then
    echo "✓ Project listing works correctly"
else
    echo "✗ Project listing failed"
fi

# Reset counter for agent's use
rm -f /tmp/cc_projects_calls

# Create a workspace marker
echo "setup_complete" > /workspace/.setup_done
echo "Mock environment ready. Agent may begin."