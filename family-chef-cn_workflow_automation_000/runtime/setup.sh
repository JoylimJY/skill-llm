#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Remove any stale family-chef-profile if it exists from a previous run
# (We want the agent to create it fresh with the correct schema)
if [ -f ~/.family-chef-profile.json ]; then
    rm -f ~/.family-chef-profile.json
    echo "Removed stale ~/.family-chef-profile.json"
fi

echo "Setup complete. Workspace ready."
echo "Agent task environment initialized."