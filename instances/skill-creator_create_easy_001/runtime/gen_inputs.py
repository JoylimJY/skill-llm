#!/usr/bin/env python3
import os
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
import random

# Set seed for deterministic generation
random.seed(42)

# Create a text-based PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font('Arial', 'B', 16)
pdf.cell(40, 10, 'MARKER_TEXT_PDF_DOCUMENT')
pdf.ln(20)
pdf.set_font('Arial', '', 12)
pdf.cell(0, 10, 'This is a text-based PDF with extractable content.')
pdf.ln(10)
pdf.cell(0, 10, 'Important data: Order #12345, Amount: $99.99')
pdf.ln(10)
pdf.cell(0, 10, 'Contact: john.doe@example.com, Phone: (555) 123-4567')
pdf.output('text_based.pdf', 'F')

# Create a simple image that looks like a scanned document
img = Image.new('RGB', (600, 400), color='white')
draw = ImageDraw.Draw(img)

try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    small_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
except:
    font = ImageFont.load_default()
    small_font = ImageFont.load_default()

draw.text((50, 50), 'MARKER_IMAGE_PDF_DOCUMENT', font=font, fill='black')
draw.text((50, 100), 'This is a scanned document image.', font=small_font, fill='black')
draw.text((50, 130), 'Invoice #67890, Total: $149.50', font=small_font, fill='black')
draw.text((50, 160), 'Email: jane.smith@company.com', font=small_font, fill='black')
draw.text((50, 190), 'Date: 2024-01-15', font=small_font, fill='black')

img.save('scanned_document.png')

# Convert the image to PDF (simulating a scanned PDF)
img_pdf = Image.new('RGB', (600, 400), color='white')
img_pdf.paste(img)
img_pdf.save('image_based.pdf')

print('Generated input files: text_based.pdf, image_based.pdf')