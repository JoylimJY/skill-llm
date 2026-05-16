#!/bin/bash
set -e

# Ensure csvkit tools are on PATH
which csvstack || echo "WARNING: csvstack not found"
which csvjoin  || echo "WARNING: csvjoin not found"
which jq       || echo "WARNING: jq not found"

# Ensure workspace is writable
chmod -R 755 /workspace

echo "Setup complete."