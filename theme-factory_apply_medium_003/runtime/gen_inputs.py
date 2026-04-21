#!/usr/bin/env python3
import json
import os

# Create themes directory
os.makedirs('themes', exist_ok=True)

# Define Ocean Depths theme
ocean_depths = {
    "name": "Ocean Depths",
    "description": "Professional and calming maritime theme",
    "colors": {
        "primary": "#1a4d6d",
        "secondary": "#2d7a99",
        "accent": "#2d7a99",
        "background": "#e8f4f8",
        "text": "#1a1a1a"
    },
    "fonts": {
        "header": "Segoe UI",
        "body": "Open Sans"
    }
}

# Save Ocean Depths theme
with open('themes/ocean_depths.json', 'w') as f:
    json.dump(ocean_depths, f, indent=2)

# Create other theme files (minimal)
other_themes = [
    {"name": "Sunset Boulevard", "colors": {"primary": "#ff6b35", "secondary": "#f7931e", "accent": "#fdb833", "background": "#fff5e6", "text": "#1a1a1a"}, "fonts": {"header": "Georgia", "body": "Lato"}},
    {"name": "Forest Canopy", "colors": {"primary": "#2d5016", "secondary": "#558b2f", "accent": "#7cb342", "background": "#f1f8e9", "text": "#1a1a1a"}, "fonts": {"header": "Trebuchet MS", "body": "Verdana"}},
    {"name": "Modern Minimalist", "colors": {"primary": "#333333", "secondary": "#666666", "accent": "#999999", "background": "#f5f5f5", "text": "#1a1a1a"}, "fonts": {"header": "Arial", "body": "Helvetica"}},
    {"name": "Golden Hour", "colors": {"primary": "#d4a574", "secondary": "#c9a961", "accent": "#e6c9a8", "background": "#fef9f3", "text": "#1a1a1a"}, "fonts": {"header": "Garamond", "body": "Calibri"}},
    {"name": "Arctic Frost", "colors": {"primary": "#4a90e2", "secondary": "#357abd", "accent": "#7cb9e8", "background": "#ecf0f7", "text": "#1a1a1a"}, "fonts": {"header": "Courier New", "body": "Consolas"}},
    {"name": "Desert Rose", "colors": {"primary": "#c9a9a0", "secondary": "#d4b5ad", "accent": "#e0c4bc", "background": "#faf6f3", "text": "#1a1a1a"}, "fonts": {"header": "Palatino", "body": "Georgia"}},
    {"name": "Tech Innovation", "colors": {"primary": "#00d4ff", "secondary": "#0099cc", "accent": "#ff0080", "background": "#0a0e27", "text": "#ffffff"}, "fonts": {"header": "Roboto", "body": "Ubuntu"}},
    {"name": "Botanical Garden", "colors": {"primary": "#6ba547", "secondary": "#8bc34a", "accent": "#9ccc65", "background": "#f5f9f0", "text": "#1a1a1a"}, "fonts": {"header": "Segoe UI", "body": "Tahoma"}},
    {"name": "Midnight Galaxy", "colors": {"primary": "#1a1a3e", "secondary": "#2d2d5f", "accent": "#6a5acd", "background": "#0f0f1e", "text": "#e0e0e0"}, "fonts": {"header": "Impact", "body": "Lucida Console"}}
]

for theme in other_themes:
    filename = 'themes/' + theme['name'].lower().replace(' ', '_') + '.json'
    with open(filename, 'w') as f:
        json.dump(theme, f, indent=2)

# Create sample HTML slides
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Presentation Slides</title>
</head>
<body>
    <div class="slide">
        <h1>Slide 1: Introduction</h1>
        <p>This is the first slide of the presentation.</p>
    </div>
    <div class="slide">
        <h1>Slide 2: Content</h1>
        <p>This slide contains important information.</p>
    </div>
    <div class="slide">
        <h1>Slide 3: Conclusion</h1>
        <p>Thank you for your attention.</p>
    </div>
</body>
</html>"""

with open('slides.html', 'w') as f:
    f.write(html_content)

# Create theme showcase PDF reference file (text-based placeholder)
with open('theme-showcase.pdf', 'w') as f:
    f.write("THEME SHOWCASE - Available Themes:\n")
    f.write("1. Ocean Depths - Professional and calming maritime theme\n")
    f.write("2. Sunset Boulevard - Warm and vibrant sunset colors\n")
    f.write("3. Forest Canopy - Natural and grounded earth tones\n")
    f.write("4. Modern Minimalist - Clean and contemporary grayscale\n")
    f.write("5. Golden Hour - Rich and warm autumnal palette\n")
    f.write("6. Arctic Frost - Cool and crisp winter-inspired theme\n")
    f.write("7. Desert Rose - Soft and sophisticated dusty tones\n")
    f.write("8. Tech Innovation - Bold and modern tech aesthetic\n")
    f.write("9. Botanical Garden - Fresh and organic garden colors\n")
    f.write("10. Midnight Galaxy - Dramatic and cosmic deep tones\n")

print("Input files generated successfully")
