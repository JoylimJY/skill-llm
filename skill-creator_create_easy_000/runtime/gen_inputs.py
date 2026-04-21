import os

# Create example directory structure to show what a skill looks like
os.makedirs('example-skill', exist_ok=True)
os.makedirs('example-skill/scripts', exist_ok=True)
os.makedirs('example-skill/references', exist_ok=True)

# Create example SKILL.md to show the format
with open('example-skill/SKILL.md', 'w') as f:
    f.write("""---
name: example-pdf-tool
description: Example skill for PDF operations
---

# Example PDF Tool

This is an example skill structure.

## Usage

Use this skill when working with PDF files.
""")

# Create example script
with open('example-skill/scripts/example.py', 'w') as f:
    f.write('# Example script\nprint("Hello from example script")')