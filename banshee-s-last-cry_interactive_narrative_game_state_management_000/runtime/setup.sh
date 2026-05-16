#!/bin/bash
set -e

# Ensure workspace directory permissions are correct
chmod -R 755 /workspace

# Verify reference files are present
echo "Verifying reference files..."
for f in ch00_start.md ch1a_investigate.md ch2b_suspect.md system_game_state.md system_clue_system.md system_character_info.md; do
    if [ -f "/workspace/references/$f" ]; then
        echo "  ✓ $f"
    else
        echo "  ✗ MISSING: $f"
    fi
done

echo "Setup complete. Workspace ready."
echo "Agent task: read the reference files and produce game_state.json"