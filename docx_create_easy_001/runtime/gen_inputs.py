#!/usr/bin/env python3
import os

# Create a marker file to verify the environment is set up
with open('setup_marker.txt', 'w') as f:
    f.write('Environment ready for docx generation')

print('Input files prepared')
