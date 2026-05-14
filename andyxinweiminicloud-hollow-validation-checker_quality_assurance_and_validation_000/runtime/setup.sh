#!/bin/bash
set -e

# Make tooling scripts executable
chmod +x /workspace/marketplace/tooling/scripts/run_batch.sh

echo "Setup complete. Workspace ready for audit task."
echo "Capsules in batch:"
ls /workspace/marketplace/submissions/batch_2024_Q4/*.json