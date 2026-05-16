#!/usr/bin/env bash
set -e

chmod -R 755 /workspace/project/scripts/
echo "Setup complete. Octave version:"
octave --version | head -1