#!/usr/bin/env python3
import os
import json

# Create project structure
os.makedirs('assets/images', exist_ok=True)
os.makedirs('assets/fonts', exist_ok=True)

# Create placeholder images with marker content
with open('assets/images/hero-bg.jpg', 'w') as f:
    f.write('<!-- MARKER_HERO_IMAGE_PLACEHOLDER -->')

with open('assets/images/work1.jpg', 'w') as f:
    f.write('<!-- MARKER_WORK1_IMAGE_PLACEHOLDER -->')

with open('assets/images/work2.jpg', 'w') as f:
    f.write('<!-- MARKER_WORK2_IMAGE_PLACEHOLDER -->')

with open('assets/images/work3.jpg', 'w') as f:
    f.write('<!-- MARKER_WORK3_IMAGE_PLACEHOLDER -->')

# Create project brief file
brief = {
    'designer_name': 'Alex Chen',
    'specialties': ['Film Titles', 'Brand Animations', 'Experimental Art'],
    'featured_projects': [
        {'title': 'Neon Dreams', 'category': 'Film Title', 'year': '2023'},
        {'title': 'Flux Brand Identity', 'category': 'Brand Animation', 'year': '2023'},
        {'title': 'Digital Metamorphosis', 'category': 'Experimental Art', 'year': '2024'}
    ],
    'contact': {
        'email': 'alex@alexchen.design',
        'location': 'Los Angeles, CA'
    },
    'marker_validation': 'PORTFOLIO_BRIEF_MARKER_12345'
}

with open('brief.json', 'w') as f:
    json.dump(brief, f, indent=2)

print('Input files generated successfully')