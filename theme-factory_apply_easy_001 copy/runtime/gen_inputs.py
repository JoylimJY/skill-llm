#!/usr/bin/env python3
import json

# Create a simple HTML slide deck
html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Presentation</title>
    <style>
        body { font-family: Arial; color: #000; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <div class="slide">
        <h1>Slide 1: Introduction</h1>
        <p>This is the first slide with placeholder content.</p>
    </div>
    <div class="slide">
        <h1>Slide 2: Key Points</h1>
        <p>Here are the main points to discuss.</p>
    </div>
    <div class="slide">
        <h1>Slide 3: Conclusion</h1>
        <p>Thank you for your attention.</p>
    </div>
</body>
</html>'''

with open('slides.html', 'w') as f:
    f.write(html_content)

# Create theme showcase PDF reference (as text file for simplicity)
theme_showcase = '''THEME SHOWCASE - Available Themes:

1. Ocean Depths - Professional and calming maritime theme
2. Sunset Boulevard - Warm and vibrant sunset colors
3. Forest Canopy - Natural and grounded earth tones
4. Modern Minimalist - Clean and contemporary grayscale
5. Golden Hour - Rich and warm autumnal palette
6. Arctic Frost - Cool and crisp winter-inspired theme
7. Desert Rose - Soft and sophisticated dusty tones
8. Tech Innovation - Bold and modern tech aesthetic
9. Botanical Garden - Fresh and organic garden colors
10. Midnight Galaxy - Dramatic and cosmic deep tones
'''

with open('theme-showcase.txt', 'w') as f:
    f.write(theme_showcase)

# Create themes directory with Ocean Depths theme
import os
os.makedirs('themes', exist_ok=True)

ocean_depths_theme = {
    "name": "Ocean Depths",
    "colors": {
        "primary": "#1a3a52",
        "secondary": "#2d5a7b",
        "accent": "#4a90a4",
        "background": "#e8f4f8"
    },
    "fonts": {
        "header": "Segoe UI",
        "body": "Calibri"
    }
}

with open('themes/ocean_depths.json', 'w') as f:
    json.dump(ocean_depths_theme, f, indent=2)

print("Input files created successfully")
