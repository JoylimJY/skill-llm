#!/usr/bin/env bash
set -e

# Ensure the /clean-csv command is executable and accessible
chmod +x /usr/local/bin/clean-csv

# Verify it works
/usr/local/bin/clean-csv --help > /dev/null 2>&1 && echo "clean-csv is ready." || echo "WARNING: clean-csv check failed."

echo "Workspace setup complete."
ls /workspace/hospital_data/exports/raw/