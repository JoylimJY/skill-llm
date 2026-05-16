#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace
chmod 644 /workspace/company/hr/relocation/incoming_hires_q1_2025.json

echo "Setup complete."