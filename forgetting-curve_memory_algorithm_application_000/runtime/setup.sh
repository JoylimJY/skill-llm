#!/bin/bash
set -e

# Make forgetting_curve importable from /workspace
cd /workspace
export PYTHONPATH="/workspace:$PYTHONPATH"

# Ensure the module is importable
python -c "from forgetting_curve import ForgettingCurve, SpacedRepetitionScheduler, batch_decay; print('Module OK')"

echo "Setup complete."