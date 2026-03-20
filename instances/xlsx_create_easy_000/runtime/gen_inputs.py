#!/usr/bin/env python3

# This script creates input files for the expense tracker task
# No input files needed - user will create from scratch

import os

# Create a marker file to verify the workspace is set up correctly
with open('workspace_ready.txt', 'w') as f:
    f.write('Workspace ready for expense tracker creation\n')
    f.write('Expected output: expenses_jan2024.xlsx\n')

print('Input files generated successfully')
