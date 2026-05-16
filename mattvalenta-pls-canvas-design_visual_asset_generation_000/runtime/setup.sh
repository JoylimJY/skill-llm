#!/bin/bash
set -e

# Verify Python packages are available
python3 -c "from PIL import Image, ImageDraw, ImageFont; print('PIL OK')"
python3 -c "from fpdf import FPDF; print('fpdf OK')"
python3 -c "import numpy; print('numpy OK')"

# List available fonts for agent convenience (agent must discover these)
echo "=== Available system fonts ==="
fc-list | grep -i "liberation\|dejavu\|arial" | head -20 || true

echo "Setup complete."