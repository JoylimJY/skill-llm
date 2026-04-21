import os
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Create a simple PDF with known content
def create_test_pdf():
    c = canvas.Canvas('sample_document.pdf', pagesize=letter)
    c.drawString(100, 750, 'Test Document')
    c.drawString(100, 720, 'Author: John Smith')
    c.drawString(100, 690, 'Date: 2024-01-15')
    c.drawString(100, 660, 'This document contains sample text for extraction.')
    c.drawString(100, 630, 'It includes metadata and structured content.')
    c.save()

create_test_pdf()
print('Generated sample_document.pdf')