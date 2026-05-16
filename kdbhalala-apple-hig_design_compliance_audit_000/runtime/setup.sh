#!/bin/bash
set -e

echo "Setting up StreamFlow design audit workspace..."

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Workspace ready. Raw submission at: /workspace/submissions/raw/streamflow_design_spec_v3.2.json"