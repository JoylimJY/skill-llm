#!/usr/bin/env bash
set -e

chmod +x /workspace/skills/excalidraw-diagram-generator/scripts/add-icon-to-diagram.py
chmod +x /workspace/skills/excalidraw-diagram-generator/scripts/add-arrow.py

echo "Setup complete. Scripts are executable."
tree /workspace/skills/excalidraw-diagram-generator/ 2>/dev/null || find /workspace/skills/excalidraw-diagram-generator -type f | sort