#!/bin/bash
set -e
echo 'Setting up environment for web artifacts builder task...'
# Ensure pnpm is available and updated
npm install -g pnpm@latest
echo 'Environment setup complete'