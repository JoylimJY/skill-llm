#!/bin/bash
set -e

# Ensure duckdb is executable
chmod +x /usr/local/bin/duckdb

# Verify DuckDB is working
duckdb --version

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Setup complete."