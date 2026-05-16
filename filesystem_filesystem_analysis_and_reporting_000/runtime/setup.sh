#!/bin/bash
set -e

# Ensure workspace exists and is readable
chmod -R 755 /workspace/data_landing_zone

echo "Workspace setup complete."
echo "Landing zone structure:"
find /workspace/data_landing_zone -type f | wc -l
echo "files found in data_landing_zone"