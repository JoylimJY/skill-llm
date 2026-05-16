#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key input files exist..."
ls /workspace/project_tcm_ip/phase2_interview/raw_notes/
ls /workspace/project_tcm_ip/phase1_research/

echo "Setup complete. Agent workspace is ready."