#!/bin/bash
set -e

# Ensure the validate.py script is executable
chmod +x /root/flutter-schema/scripts/validate.py

# Verify the script exists and is runnable
python /root/flutter-schema/scripts/validate.py --help 2>/dev/null || true

# Ensure workspace has correct permissions
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."
echo "validate.py location: /root/flutter-schema/scripts/validate.py"