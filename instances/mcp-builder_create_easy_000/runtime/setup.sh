#!/bin/bash
set -e

# Make gen_inputs_script executable and run it
chmod +x gen_inputs_script
python3 gen_inputs_script

echo "Setup completed"