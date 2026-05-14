#!/bin/bash
set -e

# Make the prayer_times.py script executable
chmod +x /workspace/prayer_times.py

# Verify python and key packages are available
python3 -c "import requests; print('requests OK')"
python3 -c "from thefuzz import process; print('thefuzz OK')"

echo "Setup complete. Workspace ready."
echo "prayer_times.py is executable at /workspace/prayer_times.py"