#!/bin/bash
set -e

# Make scripts executable
chmod +x gen_inputs_script
chmod +x eval_script

# Generate input files
python3 gen_inputs_script

echo 'Setup completed successfully.'