#!/bin/bash
# Create canvas-fonts directory with available system fonts
mkdir -p canvas-fonts
cp /usr/share/fonts/truetype/dejavu/*.ttf canvas-fonts/ 2>/dev/null || true
cp /usr/share/fonts/truetype/liberation/*.ttf canvas-fonts/ 2>/dev/null || true
echo 'Fonts available for canvas design task'