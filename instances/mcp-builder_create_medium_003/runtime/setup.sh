#!/bin/bash
set -e

# Make gen_inputs_script executable and run it
chmod +x gen_inputs_script
python3 gen_inputs_script

# Install Node.js dependencies
npm install

# Create src directory structure
mkdir -p src/tools
mkdir -p src/services
mkdir -p src/schemas

echo "Setup complete"