#!/usr/bin/env python3
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image, ImageDraw, ImageFont
import subprocess

# Install reportlab if not available
try:
    import reportlab
except ImportError:
    subprocess.run(['pip', 'install', 'reportlab'], check=True)
    import reportlab

# Create a text-based PDF
c = canvas.Canvas('sample_text.pdf', pagesize=letter)
c.drawString(100, 750, 'MARKER_TEXT_PDF_123')
c.drawString(100, 700, 'This is a sample PDF document for testing.')
c.drawString(100, 650, 'It contains multiple lines of text.')
c.drawString(100, 600, 'The skill should extract this content successfully.')
c.showPage()
c.save()

# Create an image-based PDF (for OCR testing)
img = Image.new('RGB', (600, 800), color='white')
draw = ImageDraw.Draw(img)

# Use default font
font_size = 24
try:
    # Try to use a better font if available
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', font_size)
except:
    font = ImageFont.load_default()

draw.text((50, 100), 'MARKER_IMAGE_PDF_456', fill='black', font=font)
draw.text((50, 150), 'This PDF contains image-based text.', fill='black', font=font)
draw.text((50, 200), 'OCR should be used to extract this.', fill='black', font=font)
draw.text((50, 250), 'Testing image text extraction.', fill='black', font=font)

img.save('temp_image.png')

# Convert image to PDF
from reportlab.lib.utils import ImageReader
c2 = canvas.Canvas('sample_image.pdf', pagesize=letter)
c2.drawImage('temp_image.png', 0, 0, width=600, height=800)
c2.save()

# Clean up temp image
os.remove('temp_image.png')

print('Generated sample_text.pdf and sample_image.pdf')