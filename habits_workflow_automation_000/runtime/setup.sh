#!/usr/bin/env bash
set -e

# Ensure habits directory does NOT pre-exist (agent must create it)
rm -rf /root/habits

echo "Setup complete. Workspace ready."
ls /root/