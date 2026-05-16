#!/bin/bash
set -e

echo "Setting up competition workspace..."

# Ensure results directory is writable
chmod -R 755 /workspace/competition_admin/results/

# Create the output directory where the agent should write results
mkdir -p /workspace/competition_admin/results/

echo "Setup complete. The agent should process:"
echo "  - /workspace/competition_admin/participants/teams.json"
echo "  - /workspace/competition_admin/schedule/groups.json"
echo "  - /workspace/competition_admin/results/group_stage_raw.json"
echo "And produce: tournament_results.json"