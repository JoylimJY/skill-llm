#!/bin/bash
set -e

# Make the main script executable
chmod +x /workspace/scripts/guess_number.py

# Set the deterministic seed for the game engine (used during testing)
export GUESS_SEED=42

# Verify the script runs
echo "Verifying game engine script..."
python /workspace/scripts/guess_number.py --help 2>/dev/null || true

echo "Setup complete. GUESS_SEED=42 is active for this session."
echo "Agents: The game engine script is at scripts/guess_number.py"