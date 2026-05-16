#!/bin/bash
set -e

# Make integration test script executable
chmod +x /workspace/servo_project/tests/integration/test_loop.sh
chmod +x /workspace/servo_project/scripts/deploy.sh

echo "Workspace setup complete."
echo "Problem file is at: /workspace/servo_project/firmware/src/servo_controller_draft.c"