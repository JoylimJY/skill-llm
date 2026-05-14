#!/bin/bash
set -e

# Ensure reference files are readable
chmod 644 /workspace/references/location-normalizer-input.schema.json
chmod 644 /workspace/references/location-normalizer-output.schema.json
chmod 644 /workspace/references/india-location-aliases-v1.json
chmod 644 /workspace/leads/raw/messy_leads_for_normalization.json

echo "Setup complete. Workspace ready."