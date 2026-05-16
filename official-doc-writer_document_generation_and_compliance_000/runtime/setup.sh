#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/.trae/skills/official-doc-writer/scripts/generate_official_doc.py
chmod +x /workspace/.trae/skills/official-doc-writer/scripts/install_fonts.py

# Add the skill scripts to PYTHONPATH so imports work
export PYTHONPATH="/workspace/.trae/skills/official-doc-writer:${PYTHONPATH}"

# Create a convenience symlink so agent can also use scripts/ directly from workspace
ln -sf /workspace/.trae/skills/official-doc-writer/scripts /workspace/scripts 2>/dev/null || true

echo "Setup complete."