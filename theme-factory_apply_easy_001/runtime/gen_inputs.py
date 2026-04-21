import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_theme_showcase_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    text = c.beginText(72, 720)  # start near top-left
    text.setFont("Helvetica-Bold", 16)
    text.textLine("Theme Showcase")

    themes = [
        "Ocean Depths",
        "Sunset Boulevard",
        "Forest Canopy",
        "Modern Minimalist",
        "Golden Hour",
        "Arctic Frost",
        "Desert Rose",
        "Tech Innovation",
        "Botanical Garden",
        "Midnight Galaxy"
    ]

    text.setFont("Helvetica", 12)
    for i, theme in enumerate(themes, 1):
        text.textLine(f"{i}. {theme}")

    c.drawText(text)
    c.showPage()
    c.save()


def create_presentation_md(filename):
    content = (
        "# Slide Deck Example\n"
        "\n"
        "## Introduction\n"
        "Welcome to our presentation about theme styling.\n"
        "\n"
        "## Overview\n"
        "This deck will demonstrate applying the Sunset Boulevard theme.\n"
        "\n"
        "## Conclusion\n"
        "Thank you for reviewing our themes!\n"
        "\n"
        "[MARKER-PRESENTATION-FILE]"
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    create_theme_showcase_pdf("theme-showcase.pdf")
    create_presentation_md("presentation.md")

if __name__ == "__main__":
    main()
