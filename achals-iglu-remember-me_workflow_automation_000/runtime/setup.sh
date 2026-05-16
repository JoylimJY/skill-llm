#!/bin/bash
set -e

# Set workspace permissions
chmod -R 755 /workspace

# Create a simulated "today" marker the agent can reference
echo "2025-03-15" > /workspace/config/today.txt

echo "Setup complete. Today's date anchor: 2025-03-15"