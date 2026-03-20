#!/usr/bin/env python3
import os
import random

# Set deterministic seed
random.seed(42)

# Create examples directory structure to match skill
os.makedirs('examples', exist_ok=True)

# Create the 3p-updates.md file with marker content
with open('examples/3p-updates.md', 'w') as f:
    f.write('''## Instructions
You are being asked to write a 3P update. 3P updates stand for "Progress, Plans, Problems." The main audience is for executives, leadership, other teammates, etc. They're meant to be very succinct and to-the-point: think something you can read in 30-60sec or less.

3Ps can cover a team of any size. They represent the work of the team across a time period, almost always one week. They include three sections:
1) Progress: what the team has accomplished over the time period
2) Plans: what the team plans to do over the next time period
3) Problems: anything that is slowing the team down

## Formatting

The format is always the same, very strict formatting. Pick an emoji that captures the vibe of the team.

[pick an emoji] [Team Name] (Dates Covered)
Progress: [1-3 sentences of content]
Plans: [1-3 sentences of content]
Problems: [1-3 sentences of content]

Each section should be no more than 1-3 sentences: clear, to the point. It should be data-driven, and generally include metrics where possible. The tone should be very matter-of-fact.

<!-- MARKER_3P_GUIDELINES_LOADED -->
''')

# Create other example files to match skill structure
with open('examples/company-newsletter.md', 'w') as f:
    f.write('# Company Newsletter Guidelines\n<!-- MARKER_NEWSLETTER_FILE -->')

with open('examples/faq-answers.md', 'w') as f:
    f.write('# FAQ Guidelines\n<!-- MARKER_FAQ_FILE -->')
    
with open('examples/general-comms.md', 'w') as f:
    f.write('# General Comms Guidelines\n<!-- MARKER_GENERAL_FILE -->')

print('Generated input files successfully')