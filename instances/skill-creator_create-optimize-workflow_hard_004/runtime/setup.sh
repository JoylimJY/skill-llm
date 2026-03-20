#!/bin/bash
set -e

# Setup virtual display for PDF generation
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &

# Create directories
mkdir -p /tmp/skill-workspace
mkdir -p /tmp/reports

echo "Environment setup complete"