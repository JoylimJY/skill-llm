#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/scan.py
chmod +x /workspace/automation/cron_scan.sh

# Ensure the workspace is clean of any pre-existing scanner config
# (agent must create it from scratch)
rm -rf ~/.config/network-scanner/

# Verify nmap and dig are available
which nmap >/dev/null 2>&1 && echo "✓ nmap available" || echo "✗ nmap NOT found"
which dig  >/dev/null 2>&1 && echo "✓ dig available"  || echo "✗ dig NOT found"

# Verify scan.py is functional
python3 /workspace/scripts/scan.py --help >/dev/null 2>&1 && echo "✓ scan.py OK" || echo "✗ scan.py failed"

echo "Setup complete."