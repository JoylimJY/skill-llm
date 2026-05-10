#!/usr/bin/env bash
set -euo pipefail

echo "=== Setup: Initializing workspace ==="

# Ensure skill_context scripts are executable
find /workspace/skill_context/scripts -name "*.py" -exec chmod +x {} \;

# Verify key tools are available
python3 -c "import markitdown; print('markitdown OK')" 2>/dev/null || echo "WARN: markitdown not importable directly"
python3 -m markitdown --help > /dev/null 2>&1 && echo "markitdown CLI OK" || echo "WARN: markitdown CLI not ready"

# Verify the template file was generated
if [ -f /workspace/pipeline_update_template.pptx ]; then
    echo "✓ pipeline_update_template.pptx exists ($(stat -c%s /workspace/pipeline_update_template.pptx) bytes)"
else
    echo "ERROR: pipeline_update_template.pptx not found"
    exit 1
fi

# Verify content brief exists
if [ -f /workspace/data/q3_pipeline_content.txt ]; then
    echo "✓ Q3 content brief exists"
else
    echo "ERROR: Q3 content brief not found"
    exit 1
fi

echo "=== Setup complete ==="