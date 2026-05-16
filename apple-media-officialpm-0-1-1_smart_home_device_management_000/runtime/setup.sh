#!/bin/bash
set -e

# Make all scripts executable
chmod +x /workspace/skills/apple-media/scripts/scan.sh
chmod +x /workspace/skills/apple-media/scripts/scan-hosts.sh
chmod +x /workspace/skills/apple-media/scripts/scan-json.js
chmod +x /workspace/skills/apple-media/scripts/connect.sh
chmod +x /workspace/skills/apple-media/scripts/volume.sh
chmod +x /workspace/skills/airfoil/airfoil.sh
chmod +x /usr/local/bin/atvremote

# Verify mock atvremote works
echo "=== atvremote scan test ==="
atvremote scan | head -5

# Verify scan-json.js parses correctly
echo "=== scan-json.js test ==="
node /workspace/skills/apple-media/scripts/scan-json.js 3 | head -10

echo "=== Setup complete ==="