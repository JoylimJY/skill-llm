#!/bin/bash
set -e

echo "=== Setup: Recursive Generosity Protocol Sandbox ==="

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify the canonical v1 file is present and record its hash for tamper detection in eval
md5sum /workspace/references/delta9-wp-003_recursive_generosity_v1.md > /workspace/.v1_canonical_hash

echo "Canonical v1 hash recorded: $(cat /workspace/.v1_canonical_hash)"
echo "Setup complete. Workspace ready."