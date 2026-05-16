#!/bin/bash
set -e

# Make archive scripts executable (distractor)
chmod +x /workspace/archive/v1/run_pipeline.sh
chmod +x /workspace/archive/v2/run_pipeline.sh
chmod +x /workspace/scripts/upload_results.sh

# Set the WARN_AS_ERROR environment variable so the lint gate in tdd.py is active
# This is exported into /etc/environment so it persists for the agent session
echo "export WARN_AS_ERROR=1" >> /etc/bash.bashrc
export WARN_AS_ERROR=1

echo "Setup complete. WARN_AS_ERROR=1 is active."