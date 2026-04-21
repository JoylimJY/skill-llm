import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import random
import datetime

random.seed(12345)

os.makedirs('input_files', exist_ok=True)

# Utility to draw text on images

def create_receipt_image(filename, vendor, date_str, amount_str, handwritten=False):
    img = Image.new('RGB', (400, 200), color='white')
    d = ImageDraw.Draw(img)
    fnt = ImageFont.load_default()

    # Vendor at top
    d.text((10, 10), vendor, font=fnt, fill=(0, 0, 0))

    # Date - optionally handwritten style simulated by offset
    if handwritten:
        for i, ch in enumerate(date_str):
            d.text((10 + i*12 + random.randint(-2,2), 40 + random.randint(-2,2)), ch, font=fnt, fill=(0,0,0))
    else:
        d.text((10, 40), f"Date: {date_str}", font=fnt, fill=(0, 0, 0))

    # Amount
    d.text((10, 80), f"Total: ${amount_str}", font=fnt, fill=(0, 0, 0))

    # Description
    d.text((10, 110), "Office Supplies Purchase", font=fnt, fill=(0, 0, 0))

    img.save(os.path.join('input_files', filename))

# Create 3 receipt images (JPG, PNG) with handwritten and typed dates
create_receipt_image('IMG_1234.jpg', 'Staples', '2023-11-10', '45.60', handwritten=True)
create_receipt_image('receipt_office.png', 'Office Depot', '2022-07-05', '78.22', handwritten=False)
create_receipt_image('travel_receipt.png', 'Delta Airlines', '2024-01-15', '312.99', handwritten=True)

# Create PDF invoices with multiple pages and textual invoice info
# Invoices have vendor at top, invoice number, date, amount, and description

def create_invoice_pdf(filename, vendor, invoice_num, date_str, amount_str, description, multipage=False):
    c = canvas.Canvas(os.path.join('input_files', filename), pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, vendor)
    c.setFont("Helvetica", 12)
    c.drawString(72, height - 100, f"Invoice #: {invoice_num}")
    c.drawString(72, height - 120, f"Invoice Date: {date_str}")
    c.drawString(72, height - 140, f"Amount Due: ${amount_str}")
    c.drawString(72, height - 160, f"Description: {description}")

    if multipage:
        c.showPage()
        c.setFont("Helvetica", 12)
        c.drawString(72, height - 72, "Additional Terms and Conditions")
        c.drawString(72, height - 90, "Thank you for your business.")
    c.save()

create_invoice_pdf('invoice_adobe.pdf', 'Adobe', 'INV-20231101', '2023-11-01', '52.99', 'Creative Cloud Subscription', multipage=False)
create_invoice_pdf('invoice_amazon.pdf', 'Amazon', '123-4567890-1234567', '2023-12-15', '127.45', 'Office Supplies', multipage=True)
create_invoice_pdf('invoice_stripe.pdf', 'Stripe', 'STR-998877', '2024-02-10', '250.00', 'Monthly Payment Processing', multipage=False)

# Create some duplicate files with different names

import shutil
shutil.copyfile('input_files/invoice_adobe.pdf', 'input_files/invoice_adobe_duplicate.pdf')
shutil.copyfile('input_files/IMG_1234.jpg', 'input_files/invoice.pdf')

# Create a PDF with missing vendor info to be flagged
c = canvas.Canvas('input_files/unknown_vendor.pdf', pagesize=letter)
c.setFont("Helvetica", 12)
c.drawString(72, 720, "Invoice #: UNK-001")
c.drawString(72, 700, "Date: 2024-03-05")
c.drawString(72, 680, "Total: $99.99")
c.save()

# Create a PNG file with minimal info (to test fallback)
img = Image.new('RGB', (300,100), 'white')
d = ImageDraw.Draw(img)
d.text((10, 10), "No invoice info here", font=ImageFont.load_default(), fill=(0,0,0))
img.save('input_files/unknown.png')

# Files created:
# input_files/
# - invoice_adobe.pdf
# - invoice_amazon.pdf
# - invoice_stripe.pdf
# - invoice_adobe_duplicate.pdf
# - IMG_1234.jpg
# - receipt_office.png
# - travel_receipt.png
# - invoice.pdf (duplicate of IMG_1234.jpg)
# - unknown_vendor.pdf
# - unknown.png
