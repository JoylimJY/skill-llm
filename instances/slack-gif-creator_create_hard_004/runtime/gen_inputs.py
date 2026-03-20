#!/usr/bin/env python3
# Generate deterministic input files with marker content
import os
import random

# Set deterministic seed
random.seed(42)

# Create a reference requirements file
with open('requirements.txt', 'w') as f:
    f.write('pillow==10.0.0\n')
    f.write('imageio==2.31.1\n')
    f.write('numpy==1.24.3\n')
    f.write('# MARKER_REQUIREMENTS_42\n')

# Create a simple test image for reference
from PIL import Image, ImageDraw

# Create a star pattern reference image
ref_img = Image.new('RGB', (64, 64), (20, 20, 40))
draw = ImageDraw.Draw(ref_img)

# Draw some reference stars
for i in range(5):
    x = 10 + i * 10
    y = 20 + (i % 2) * 20
    draw.ellipse([x-2, y-2, x+2, y+2], fill=(255, 255, 200))

ref_img.save('star_reference.png')

print('Generated input files with markers')