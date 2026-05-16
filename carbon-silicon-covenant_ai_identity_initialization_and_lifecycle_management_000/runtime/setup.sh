#!/bin/bash
set -e

# Make birthday script executable
chmod +x /workspace/modules/birthday/scripts/calculate_age.py

# Set MOCK_TODAY so the birthday calculation is deterministic:
# birth_date = 2025-01-01, mock_today = 2025-01-21  =>  20 days  =>  "萌芽" stage
export MOCK_TODAY="2025-01-21"
echo "export MOCK_TODAY=2025-01-21" >> /etc/environment
echo "export MOCK_TODAY=2025-01-21" >> /root/.bashrc
echo "export MOCK_TODAY=2025-01-21" >> /root/.profile

# Verify the script works with the mock date
echo "=== Verifying birthday script ==="
MOCK_TODAY=2025-01-21 python3 /workspace/modules/birthday/scripts/calculate_age.py 2025-01-01 --milestones

echo ""
echo "=== Setup complete. MOCK_TODAY=2025-01-21 ==="
echo "The agent should set MOCK_TODAY=2025-01-21 when calling calculate_age.py"
echo "Or use --today 2025-01-21 flag"