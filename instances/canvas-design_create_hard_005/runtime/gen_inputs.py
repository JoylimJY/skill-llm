#!/usr/bin/env python3
import os
import random

# Set deterministic seed
random.seed(42)

# Create canvas-fonts directory with some basic font files
os.makedirs('canvas-fonts', exist_ok=True)

# Create a marker file to verify the skill was executed
with open('task_marker.txt', 'w') as f:
    f.write('DIGITAL_ARCHAEOLOGY_TASK_MARKER_2024')

print('Generated input files for digital archaeology art task')
