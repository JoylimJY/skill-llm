#!/usr/bin/env python3

import os
import random
from pathlib import Path

# Set deterministic seed
random.seed(42)

# Create a simple requirements file to indicate this is a branding project
with open('brand_project_requirements.txt', 'w') as f:
    f.write('# Anthropic Brand Guidelines Project\n')
    f.write('# Marker: BRAND_PROJECT_INIT_2024\n')
    f.write('Target: PowerPoint presentation with complete brand identity\n')
    f.write('Slides needed: 5 slides minimum\n')
    f.write('Include: Colors, typography, examples, usage guidelines\n')
    f.write('Theme requirements: Both light and dark examples\n')
    f.write('Quality: Production-ready for Q1 rollout\n')
    f.write('# Verification marker: ANTHROPIC_BRAND_SPEC_v1.2\n')

# Create a style reference file with expected brand elements
with open('expected_brand_elements.txt', 'w') as f:
    f.write('Expected Brand Colors:\n')
    f.write('Dark: #141413 (Primary text and dark backgrounds)\n')
    f.write('Light: #faf9f5 (Light backgrounds)\n')
    f.write('Mid Gray: #b0aea5 (Secondary elements)\n')
    f.write('Light Gray: #e8e6dc (Subtle backgrounds)\n')
    f.write('Orange: #d97757 (Primary accent)\n')
    f.write('Blue: #6a9bcc (Secondary accent)\n')
    f.write('Green: #788c5d (Tertiary accent)\n')
    f.write('\nExpected Typography:\n')
    f.write('Headings: Poppins (Arial fallback)\n')
    f.write('Body: Lora (Georgia fallback)\n')
    f.write('\n# Validation marker: EXPECTED_BRAND_CONFIG_CHECK\n')

print('Generated input files for Anthropic brand guidelines project')