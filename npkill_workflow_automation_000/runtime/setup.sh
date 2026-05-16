#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify npkill is installed and accessible
echo "Verifying npkill installation..."
npkill --version || echo "npkill version check done"

# Verify the workspace was generated correctly
echo ""
echo "Verifying .next folders exist before agent runs:"
find /workspace/projects -name ".next" -type d | sort

echo ""
echo "Verifying node_modules exist (these should NOT be deleted by the targeted scan):"
find /workspace/projects -name "node_modules" -type d | sort

echo ""
echo "Setup complete. Agent should:"
echo "1. Run a dry-run scan of /workspace/projects for .next folders, saving output to cleanup_preview.txt"
echo "2. Delete all .next folders under /workspace/projects (not node_modules, not vendor/)"