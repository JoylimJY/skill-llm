#!/bin/bash
set -e

chmod +x /workspace/scripts/ofd_to_text.py
chmod +x /workspace/scripts/ofd_to_markdown.py
chmod +x /workspace/scripts/install_dependencies.py

echo "Setup complete. Workspace ready."
ls /workspace/
ls /workspace/scripts/
ls /workspace/incoming_documents/2024/Q1/