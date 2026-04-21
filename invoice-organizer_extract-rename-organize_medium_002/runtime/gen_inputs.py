import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont

os.makedirs('receipts2024', exist_ok=True)

# Fixed seed for deterministic behavior

# Create 3 PDF invoices with invoice info
pdf_data = [
    {
        'filename': 'invoice(1).pdf',
        'date': '2024-02-15',
        'vendor': 'Adobe',
        'invoice_number': 'INV-1001',
        'amount': '52.99',
        'description': 'Photoshop License'
    },
    {
        'filename': 'expense_20240110.pdf',
        'date': '2024-01-10',
        'vendor': 'Amazon',
        'invoice_number': 'AMZ-9988',
        'amount': '127.45',
        'description': 'Office Supplies'
    },
    {
        'filename': 'random_invoice.pdf',
        'date': '2024-02-05',
        'vendor': 'Stripe',
        'invoice_number': 'STR-5555',
        'amount': '300.00',
        'description': 'Payment Processing'
    }
]

from reportlab.lib.units import inch

def create_pdf_invoice(path, data):
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica", 12)

    # Vendor header
    c.drawString(72, height - 72, data['vendor'])

    # Invoice details
    c.drawString(72, height - 100, f"Invoice #: {data['invoice_number']}")
    c.drawString(72, height - 115, f"Invoice Date: {data['date']}")
    c.drawString(72, height - 130, f"Description: {data['description']}")
    c.drawString(72, height - 145, f"Amount Due: ${data['amount']}")

    c.showPage()
    c.save()

for invoice in pdf_data:
    path = os.path.join('receipts2024', invoice['filename'])
    create_pdf_invoice(path, invoice)

# Create 3 JPG image receipts with text
# Use PIL to create simple images with text at top
image_data = [
    {
        'filename': 'scan_20240201.jpg',
        'date': '2024-02-01',
        'vendor': 'Staples',
        'receipt_number': 'R-4321',
        'amount': '89.60',
        'description': 'Office Chairs'
    },
    {
        'filename': 'receipt_A123.png',
        'date': '2024-02-20',
        'vendor': 'BestBuy',
        'receipt_number': 'BB-8765',
        'amount': '234.99',
        'description': 'Monitor Purchase'
    },
    {
        'filename': 'photo_receipt.jpg',
        'date': '2024-01-25',
        'vendor': 'Uber',
        'receipt_number': 'UB-1122',
        'amount': '18.75',
        'description': 'Business Ride'
    }
]

font_path = None
try:
    # Try to load a basic font included in PIL
    from PIL import ImageFont
    font_path = ImageFont.load_default()
except Exception:
    font_path = None

for img in image_data:
    img_path = os.path.join('receipts2024', img['filename'])
    image = Image.new('RGB', (400, 200), color='white')
    d = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text_lines = [
        img['vendor'],
        f"Date: {img['date']}",
        f"Receipt #: {img['receipt_number']}",
        f"Description: {img['description']}",
        f"Total: ${img['amount']}"
    ]
    y = 10
    for line in text_lines:
        d.text((10, y), line, fill='black', font=font)
        y += 30
    image.save(img_path)
