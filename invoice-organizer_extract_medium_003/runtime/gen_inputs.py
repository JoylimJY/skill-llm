import os
from datetime import datetime
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
import random

# Deterministic seed
random.seed(42)

# Create sample PDFs with invoice content
pdfs = [
    {
        'filename': 'inv123.pdf',
        'vendor': 'Adobe',
        'date': '2024-03-15',
        'invoice_no': 'INV-123',
        'description': 'Creative Cloud Subscription',
        'amount': '52.99',
        'category': 'Software'
    },
    {
        'filename': 'bill_april.pdf',
        'vendor': 'Amazon',
        'date': '2024-04-10',
        'invoice_no': 'AMZ-456',
        'description': 'Office Keyboard',
        'amount': '78.45',
        'category': 'Office Supplies'
    },
    {
        'filename': 'receipt_march.pdf',
        'vendor': 'Delta Airlines',
        'date': '2024-03-20',
        'invoice_no': 'DL-789',
        'description': 'Business Class Ticket',
        'amount': '450.00',
        'category': 'Travel'
    }
]

# Create PDFs programmatically with minimal invoice text
class PDFInvoice(FPDF):
    def header(self):
        pass
    def footer(self):
        pass

for inv in pdfs:
    pdf = PDFInvoice()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=inv['vendor'], ln=True)
    pdf.cell(0, 10, txt=f"Invoice Date: {inv['date']}", ln=True)
    pdf.cell(0, 10, txt=f"Invoice #: {inv['invoice_no']}", ln=True)
    pdf.cell(0, 10, txt=f"Description: {inv['description']}", ln=True)
    pdf.cell(0, 10, txt=f"Amount Due: ${inv['amount']}", ln=True)
    pdf.output(inv['filename'])

# Create 3 image receipts with text drawn
# Use PIL to generate images
image_receipts = [
    {
        'filename': 'IMG_001.jpg',
        'vendor': 'Staples',
        'date': '2024-03-10',
        'invoice_no': 'ST-111',
        'description': 'Printer Ink Cartridge',
        'amount': '45.99',
        'category': 'Office Supplies'
    },
    {
        'filename': 'scan_April.png',
        'vendor': 'Uber',
        'date': '2024-04-15',
        'invoice_no': 'UB-222',
        'description': 'Airport Ride',
        'amount': '35.20',
        'category': 'Travel'
    },
    {
        'filename': 'receipt_001.png',
        'vendor': 'Microsoft',
        'date': '2024-03-22',
        'invoice_no': 'MS-333',
        'description': 'Office 365 License',
        'amount': '99.99',
        'category': 'Software'
    }
]

# Use a default font
font_path = None
try:
    from PIL import ImageFont
    import pathlib
    # Try to find a default ttf font
    import sys
    import platform
    if platform.system() == 'Windows':
        font_path = 'C:/Windows/Fonts/arial.ttf'
    else:
        font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    font = ImageFont.truetype(font_path, 18)
except Exception:
    font = None

for rec in image_receipts:
    img = Image.new('RGB', (400, 180), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    lines = [
        rec['vendor'],
        f"Date: {rec['date']}",
        f"Invoice #: {rec['invoice_no']}",
        f"Description: {rec['description']}",
        f"Total: ${rec['amount']}"
    ]
    y = 10
    for line in lines:
        if font:
            d.text((10, y), line, fill=(0,0,0), font=font)
        else:
            d.text((10, y), line, fill=(0,0,0))
        y += 30
    img.save(rec['filename'])

# Create some messy filenames to test extraction
# Done by naming files as in the data provided above
