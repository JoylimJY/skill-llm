#!/usr/bin/env bash
set -e

# Make the calculator script executable
chmod +x /workspace/scripts/lunar_calculator.py

# Verify the lunardate package works correctly
python3 -c "from lunardate import LunarDate; d = LunarDate(2023, 2, 1, isLeapMonth=True); print('lunardate OK, leap test:', d.toSolarDate())"

echo "Setup complete. Workspace ready."