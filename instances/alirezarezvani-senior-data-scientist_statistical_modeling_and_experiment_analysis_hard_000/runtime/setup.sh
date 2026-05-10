#!/usr/bin/env bash
set -euo pipefail

echo "Setting up workspace permissions..."
chmod -R 755 /workspace/skill_context/scripts/

# Verify skill scripts are present
for script in experiment_designer.py feature_engineering_pipeline.py model_evaluation_suite.py; do
    if [ ! -f "/workspace/skill_context/scripts/$script" ]; then
        echo "WARNING: /workspace/skill_context/scripts/$script not found"
    else
        echo "OK: $script found"
    fi
done

# Set MLflow tracking URI to local directory
export MLFLOW_TRACKING_URI="file:///workspace/mlruns"
mkdir -p /workspace/mlruns

echo "Setup complete."