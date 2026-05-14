#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod +x /workspace/scripts/reset_db.sh
chmod +x /workspace/scripts/run_tests.sh

echo "Setup complete."