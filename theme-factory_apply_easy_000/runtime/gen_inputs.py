import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Generate theme-showcase.pdf with text listing all themes
pdf_path = "theme-showcase.pdf"
c = canvas.Canvas(pdf_path, pagesize=letter)
c.setFont("Helvetica-Bold", 16)
c.drawString(72, 720, "Theme Showcase")
c.setFont("Helvetica", 12)
themes = [
    "Ocean Depths - Professional and calming maritime theme",
    "Sunset Boulevard - Warm and vibrant sunset colors",
    "Forest Canopy - Natural and grounded earth tones",
    "Modern Minimalist - Clean and contemporary grayscale",
    "Golden Hour - Rich and warm autumnal palette",
    "Arctic Frost - Cool and crisp winter-inspired theme",
    "Desert Rose - Soft and sophisticated dusty tones",
    "Tech Innovation - Bold and modern tech aesthetic",
    "Botanical Garden - Fresh and organic garden colors",
    "Midnight Galaxy - Dramatic and cosmic deep tones"
]
y = 680
for theme in themes:
    c.drawString(72, y, theme)
    y -= 20
c.save()

# Generate input deck.md
deck_md_content = """# Sample Slide Deck\n\nWelcome to the presentation.\n\n## Agenda\n\n- Introduction\n- Main Topics\n- Conclusion\n"""

with open("deck.md", "w", encoding="utf-8") as f:
    f.write(deck_md_content)
