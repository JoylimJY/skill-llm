import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

BASE = Path('.')
BASE.mkdir(exist_ok=True)

# Deterministic marker content
marker = 'KB-MARKER-7F3A2D'
text_lines = [
    'Internal Knowledge Base Article',
    'Title: Quarterly Process Review',
    f'Marker: {marker}',
    'The article argues that the current review workflow is too slow and inconsistent.',
    'It recommends standardizing section headers, shortening repetitive background sections,',
    'and adding a clear approval checklist before publication.',
    'The article also notes that editors should separate factual corrections from style changes.'
]

# Write a plain-text source file
(BASE / 'source_article.txt').write_text('\n'.join(text_lines) + '\n', encoding='utf-8')

# Create a PDF version of the same content for evaluation robustness
pdf_path = BASE / 'source_article.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
width, height = letter
x = 72
y = height - 72
for line in text_lines:
    c.drawString(x, y, line)
    y -= 18
c.save()

# Add a tiny metadata file with expected marker information
(BASE / 'expected_marker.json').write_text('{"marker": "KB-MARKER-7F3A2D"}\n', encoding='utf-8')
