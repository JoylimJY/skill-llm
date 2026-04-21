import json

# Generate no external input files since this task is a direct generation task
# Instead, include some internal seed data for reproducibility if needed

# The prompt fully specifies the content, so no input files are needed here

# This script does not produce files but is mandatory

# Just create a README.txt with instructions for clarity
with open('README.txt', 'w') as f:
    f.write('Use the prompt to generate the 3p_update.md markdown file exactly as specified.\n')
