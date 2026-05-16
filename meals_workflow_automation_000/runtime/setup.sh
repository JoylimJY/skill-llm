#!/bin/bash
set -e

echo "Setting up meal planning task environment..."

# Ensure home directory is clean for the workspace
mkdir -p /root
chmod 755 /root

# Make sure the task brief is readable
chmod 644 /root/meal_planning_request.txt

echo "Environment ready. Agent should read /root/meal_planning_request.txt and set up ~/meals/ workspace."