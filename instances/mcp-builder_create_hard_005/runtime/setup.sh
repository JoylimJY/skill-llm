#!/bin/bash
set -e

# Install project dependencies
cd /workspace
npm install

# Create .env file for testing
echo "TODOIST_API_TOKEN=test_token_12345" > .env

# Make sure TypeScript is available
which tsc || npm install -g typescript

echo "Setup completed successfully"