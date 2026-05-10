#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up sandbox environment ==="

# Make skill scripts executable
chmod +x /workspace/skill_context/scripts/office/unpack.py 2>/dev/null || true
chmod +x /workspace/skill_context/scripts/office/pack.py 2>/dev/null || true
chmod +x /workspace/skill_context/scripts/office/soffice.py 2>/dev/null || true
chmod +x /workspace/skill_context/scripts/add_slide.py 2>/dev/null || true
chmod +x /workspace/skill_context/scripts/clean.py 2>/dev/null || true
chmod +x /workspace/skill_context/scripts/thumbnail.py 2>/dev/null || true

# Ensure workspace directories exist
mkdir -p /workspace/unpacked
mkdir -p /workspace/output

# Verify template exists
if [ ! -f /workspace/lp_briefing_template.pptx ]; then
    echo "ERROR: Template PPTX not found!"
    exit 1
fi

# Verify content brief exists
if [ ! -f /workspace/content_brief.json ]; then
    echo "ERROR: Content brief not found!"
    exit 1
fi

echo "=== Setup complete ==="
echo "Template: $(ls -lh /workspace/lp_briefing_template.pptx)"
echo "Brief:    $(ls -lh /workspace/content_brief.json)"