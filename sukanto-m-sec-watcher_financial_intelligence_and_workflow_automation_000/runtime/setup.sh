#!/usr/bin/env bash
set -e

# Ensure the fetch-filings.py script is executable
chmod +x /workspace/scripts/fetch-filings.py

# Verify Python dependencies are available
python3 -c "import requests; import dateutil; print('Dependencies OK')"

echo "Setup complete. Workspace ready."
echo "Script location: /workspace/scripts/fetch-filings.py"