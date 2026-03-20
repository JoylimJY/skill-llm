#!/bin/bash
set -e

# Set environment variables for React
export CI=true
export GENERATE_SOURCEMAP=false
export BROWSER=none

echo "Setup completed"