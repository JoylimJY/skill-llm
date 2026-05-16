#!/bin/bash
set -e

cd /workspace

# Ensure the pipeline script is executable
chmod +x scripts/pipelines/client-dashboard.py

# Ensure cache directories exist
mkdir -p .cache/client-dashboard
mkdir -p .cache/qbo-fixtures/ember-oak

# Ensure output dirs are writable
mkdir -p /root/Desktop

echo "Setup complete. Workspace ready."
echo ""
echo "Key paths:"
echo "  Pipeline:     scripts/pipelines/client-dashboard.py"
echo "  SKILL doc:    skills/client-dashboard/SKILL.md"
echo "  QBO fixture:  .cache/qbo-fixtures/ember-oak/2026-04.json"
echo "  CDC cache:    .cache/client-dashboard/  (empty — agent must seed for prior run)"