#!/usr/bin/env python3
import os

# Create canvas-fonts directory with some basic font information
os.makedirs('canvas-fonts', exist_ok=True)

# Create a simple font reference file
with open('canvas-fonts/available_fonts.txt', 'w') as f:
    f.write("DejaVu Sans\n")
    f.write("Liberation Sans\n")
    f.write("Noto Sans\n")
    f.write("Times Roman\n")

# Create a marker file to verify the task understands the concept
with open('concept_marker.txt', 'w') as f:
    f.write('DIGITAL_DETOX_CONCEPT_2024')

print("Input files generated successfully")