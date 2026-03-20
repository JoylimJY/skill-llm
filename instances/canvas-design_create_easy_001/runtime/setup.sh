#!/bin/bash
set -e

# Create fonts directory structure
mkdir -p ./canvas-fonts

# Copy system fonts to canvas-fonts directory for the skill to use
cp /usr/share/fonts/truetype/liberation/*.ttf ./canvas-fonts/ 2>/dev/null || true
cp /usr/share/fonts/truetype/dejavu/*.ttf ./canvas-fonts/ 2>/dev/null || true

# Update font cache
fc-cache -f

echo 'Setup complete'