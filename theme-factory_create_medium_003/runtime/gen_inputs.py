import os
from pptx import Presentation
from pptx.util import Inches, Pt
from PyPDF2 import PdfWriter

# Deterministic seed for stable content

# Generate a simple PPTX with 5 slides and placeholder content
prs = Presentation()
for i in range(5):
    slide = prs.slides.add_slide(prs.slide_layouts[1])  # Title and Content
    title = slide.shapes.title
    content = slide.placeholders[1]
    title.text = f"Slide {i+1} Title"
    content.text = f"This is the main body text for slide {i+1}."

prs.save("project_presentation.pptx")

# Generate a minimal theme-showcase.pdf file for viewing
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_theme_showcase():
    c = canvas.Canvas("theme-showcase.pdf", pagesize=letter)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, 700, "Theme Factory - Available Themes")
    themes = ["Ocean Depths", "Sunset Boulevard", "Forest Canopy", "Modern Minimalist", "Golden Hour",
              "Arctic Frost", "Desert Rose", "Tech Innovation", "Botanical Garden", "Midnight Galaxy"]
    y = 650
    for t in themes:
        c.setFont("Helvetica", 14)
        c.drawString(120, y, f"- {t}")
        y -= 30
    c.save()

create_theme_showcase()

# Generate theme files in 'themes/' directory
os.makedirs('themes', exist_ok=True)

# 'Ocean Depths' theme file content
ocean_depths_content = '''
name: Ocean Depths
colors:
  primary: "#004f78"
  secondary: "#007ea7"
  accent1: "#00a8cc"
  accent2: "#00bfd8"
fonts:
  header: "Arial Black, Bold"
  body: "Calibri, Regular"
'''.strip()

with open('themes/Ocean Depths.yaml', 'w') as f:
    f.write(ocean_depths_content)
