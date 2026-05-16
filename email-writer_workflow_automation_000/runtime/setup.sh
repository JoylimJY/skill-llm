#!/bin/bash
set -e

# Make the email.sh script executable
chmod +x /workspace/scripts/email.sh

echo "Setup complete. email.sh is executable."
echo "Test: bash /workspace/scripts/email.sh help"
bash /workspace/scripts/email.sh help