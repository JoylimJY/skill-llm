import os
from pathlib import Path

# Create themes directory
os.makedirs('themes', exist_ok=True)

# Fixed slide content for testing
presentation_txt = """Slide 1 Title
This is the introductory slide body.

Slide 2 Overview
Details and bullet points in slide two body.
"""

with open('presentation.txt', 'w', encoding='utf-8') as f:
    f.write(presentation_txt)

# Generate minimal theme-showcase.pdf
# Create a PDF with just a title page listing themes
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

pdf_path = 'theme-showcase.pdf'
c = canvas.Canvas(pdf_path, pagesize=letter)
c.setFont("Helvetica-Bold", 18)
c.drawString(100, 700, "Theme Showcase")
c.setFont("Helvetica", 12)
themes = [
    "Ocean Depths", "Sunset Boulevard", "Forest Canopy", "Modern Minimalist", "Golden Hour",
    "Arctic Frost", "Desert Rose", "Tech Innovation", "Botanical Garden", "Midnight Galaxy"
]
y = 670
for theme in themes:
    c.drawString(120, y, f"- {theme}")
    y -= 20
c.save()

# Theme specs data: hex colors and fonts (simplified for test)
theme_specs = {
    "Ocean Depths": {
        "colors": {"primary": "#004e7c", "secondary": "#99cfe0", "background": "#e6f2f7"},
        "fonts": {"header": "Merriweather", "body": "Open Sans"}
    },
    "Sunset Boulevard": {
        "colors": {"primary": "#d35400", "secondary": "#f39c12", "background": "#ffe6cc"},
        "fonts": {"header": "Playfair Display", "body": "Lato"}
    },
    "Forest Canopy": {
        "colors": {"primary": "#1b4d3e", "secondary": "#78a678", "background": "#dcf0e9"},
        "fonts": {"header": "Roboto Slab", "body": "Roboto"}
    },
    "Modern Minimalist": {
        "colors": {"primary": "#333333", "secondary": "#666666", "background": "#f9f9f9"},
        "fonts": {"header": "Helvetica Neue", "body": "Helvetica"}
    },
    "Golden Hour": {
        "colors": {"primary": "#b06c00", "secondary": "#f4a261", "background": "#fff3e0"},
        "fonts": {"header": "Georgia", "body": "Palatino"}
    },
    "Arctic Frost": {
        "colors": {"primary": "#2c3e50", "secondary": "#95a5a6", "background": "#ecf0f1"},
        "fonts": {"header": "Futura", "body": "Gill Sans"}
    },
    "Desert Rose": {
        "colors": {"primary": "#a5695d", "secondary": "#d7b29d", "background": "#f4e1da"},
        "fonts": {"header": "Cochin", "body": "Georgia"}
    },
    "Tech Innovation": {
        "colors": {"primary": "#0f4c81", "secondary": "#00b4d8", "background": "#caf0f8"},
        "fonts": {"header": "Montserrat", "body": "Source Sans Pro"}
    },
    "Botanical Garden": {
        "colors": {"primary": "#4a7c59", "secondary": "#a2b29f", "background": "#d9ead3"},
        "fonts": {"header": "Lora", "body": "Merriweather"}
    },
    "Midnight Galaxy": {
        "colors": {"primary": "#12163d", "secondary": "#6156a6", "background": "#222252"},
        "fonts": {"header": "Orbitron", "body": "Roboto"}
    }
}

# Write each theme spec as a text file in themes/
for name, spec in theme_specs.items():
    path = Path('themes') / f'{name.replace(" ", "_").lower()}.txt'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"Theme: {name}\n")
        f.write("Colors:\n")
        for key, val in spec['colors'].items():
            f.write(f"  {key}: {val}\n")
        f.write("Fonts:\n")
        f.write(f"  Header: {spec['fonts']['header']}\n")
        f.write(f"  Body: {spec['fonts']['body']}\n")

print("Input files generated.")
