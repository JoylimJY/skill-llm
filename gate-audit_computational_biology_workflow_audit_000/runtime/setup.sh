#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace/project_alpha/

# Verify the checkpoint file for run_B exists (binary)
if [ ! -f /workspace/project_alpha/md_simulations/equil_5ns/run_B/md_equil_runB.cpt ]; then
    echo "ERROR: run_B checkpoint missing after setup"
    exit 1
fi

# Confirm run_A has NO checkpoint (it should be absent)
if [ -f /workspace/project_alpha/md_simulations/equil_5ns/run_A/md_equil_runA.cpt ]; then
    echo "ERROR: run_A checkpoint should NOT exist"
    exit 1
fi

echo "Setup verification complete. Workspace is ready."