import os
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

os.makedirs('input', exist_ok=True)

# Generate PDF invoice
pdf_path = os.path.join('input', 'invoice1.pdf')
pdf = FPDF()
pdf.add_page()
pdf.set_font('Arial', 'B', 16)
pdf.cell(0, 10, 'Awesome Software Inc.', 0, 1)
pdf.set_font('Arial', '', 12)
pdf.cell(0, 10, 'Invoice Number: INV-00123', 0, 1)
pdf.cell(0, 10, 'Invoice Date: 2024-03-15', 0, 1)
pdf.cell(0, 10, 'Description: Software License - Pro Plan', 0, 1)
pdf.cell(0, 10, 'Amount Due: $199.99', 0, 1)
pdf.output(pdf_path)

# Generate JPG receipt image
jpg_path = os.path.join('input', 'receipt_image.jpg')
img = Image.new('RGB', (400, 200), color='white')
draw = ImageDraw.Draw(img)
# Use default font as fallback
try:
    font = ImageFont.truetype("arial.ttf", 15)
except:
    font = ImageFont.load_default()

draw.text((10, 20), "Staples Stationery", fill='black', font=font)
draw.text((10, 50), "Date: 2024/02/10", fill='black', font=font)
draw.text((10, 80), "Total: $45.50", fill='black', font=font)
draw.text((10, 110), "Description: Office Supplies", fill='black', font=font)
img.save(jpg_path)

# Generate PNG screenshot image
png_path = os.path.join('input', 'screenshot.png')
img2 = Image.new('RGB', (400, 200), color='white')
draw2 = ImageDraw.Draw(img2)
try:
    font2 = ImageFont.truetype("arial.ttf", 15)
except:
    font2 = ImageFont.load_default()

draw2.text((10, 15), "QuickBooks Payment", fill='black', font=font2)
draw2.text((10, 45), "Invoice #: QB-7890", fill='black', font=font2)
draw2.text((10, 75), "Date: March 10, 2024", fill='black', font=font2)
draw2.text((10, 105), "Amount: $320.00", fill='black', font=font2)
draw2.text((10, 135), "Service: Accounting Consultation", fill='black', font=font2)
img2.save(png_path)
