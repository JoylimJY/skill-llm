#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify key input files exist
echo "=== Verifying workspace setup ==="
for f in \
    "briefs/incoming/cloudvault_io_brief.txt" \
    "negotiations/active/cloudvault_io_thread.txt" \
    "negotiations/active/cloudvault_io_mandate.md"; do
    if [ -f "/workspace/$f" ]; then
        echo "[OK] $f"
    else
        echo "[MISSING] $f"
        exit 1
    fi
done

echo "=== Workspace ready ==="