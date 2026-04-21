import os
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
import random
import csv

random.seed(12345)

# Create PDFs with invoice text
class InvoicePDF(FPDF):
    def add_invoice(self, date, vendor, inv_num, amount, desc, category):
        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, vendor, 0, 1)
        self.set_font('Arial', '', 12)
        self.cell(0, 10, f'Invoice Number: {inv_num}', 0, 1)
        self.cell(0, 10, f'Invoice Date: {date}', 0, 1)
        self.cell(0, 10, f'Description: {desc}', 0, 1)
        self.cell(0, 10, f'Amount Due: ${amount:.2f}', 0, 1)
        self.cell(0, 10, f'Category: {category}', 0, 1)


# Create a minimal TTF font path for PIL (use default font)
# Use PIL's default font since no guarantee a system font is available

def create_receipt_image(filename, vendor, date, amount, desc):
    img = Image.new('RGB', (400, 200), color='white')
    d = ImageDraw.Draw(img)
    text = f"{vendor}\nDate: {date}\nTotal: ${amount:.2f}\n{desc}"  
    d.text((10, 10), text, fill='black')
    img.save(filename)


# Data for input generation - 8 files
invoices = [
    # Perfect PDF
    {
        'filename': 'invoice1.pdf',
        'date': '2024-03-15',
        'vendor': 'Adobe',
        'inv_num': 'INV-12345',
        'amount': 52.99,
        'desc': 'Creative Cloud',
        'category': 'Software'
    },
    # PDF missing amount (to test needs review)
    {
        'filename': 'invoice2.pdf',
        'date': '2024-02-20',
        'vendor': 'Staples',
        'inv_num': '5678',
        'amount': None,
        'desc': 'Office Supplies',
        'category': 'Office Supplies'
    },
    # JPG receipt
    {
        'filename': 'receipt1.jpg',
        'date': '2024-02-10',
        'vendor': 'Staples',
        'amount': 78.45,
        'desc': 'Printer Paper',
        'category': 'Office Supplies'
    },
    # PNG receipt missing vendor
    {
        'filename': 'receipt2.png',
        'date': '2024-03-05',
        'vendor': None,
        'amount': 123.00,
        'desc': 'Business Travel Meals',
        'category': 'Travel'
    },
    # PDF professional services
    {
        'filename': 'invoice3.pdf',
        'date': '2024-01-31',
        'vendor': 'ConsultCorp',
        'inv_num': '1001',
        'amount': 1500.00,
        'desc': 'Consulting Services',
        'category': 'Professional Services'
    },
    # JPG software expense
    {
        'filename': 'receipt3.jpg',
        'date': '2024-03-12',
        'vendor': 'Microsoft',
        'amount': 99.99,
        'desc': 'Office 365 Subscription',
        'category': 'Software'
    },
    # PNG travel missing date
    {
        'filename': 'receipt4.png',
        'date': None,
        'vendor': 'Uber',
        'amount': 34.20,
        'desc': 'Taxi Ride',
        'category': 'Travel'
    },
    # PDF with strange filename and full info
    {
        'filename': 'receipt_final.pdf',
        'date': '2024-02-28',
        'vendor': 'Amazon',
        'inv_num': 'AMZ-8888',
        'amount': 200.50,
        'desc': 'Office Chair',
        'category': 'Office Supplies'
    }
]

# Create PDFs

for inv in invoices:
    if inv['filename'].endswith('.pdf'):
        pdf = InvoicePDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        date_line = inv['date'] if inv['date'] else 'N/A'
        inv_num_line = inv.get('inv_num', 'N/A') if inv.get('inv_num') else 'N/A'
        amount = inv['amount'] if inv['amount'] is not None else None
        # Add invoice page
        pdf.add_invoice(date_line,
                        inv['vendor'] if inv['vendor'] else 'Unknown Vendor',
                        inv_num_line,
                        amount if amount else 0.00,
                        inv['desc'],
                        inv['category'])
        pdf.output(inv['filename'])

# Create images
for inv in invoices:
    if inv['filename'].endswith('.jpg') or inv['filename'].endswith('.png'):
        vendor = inv['vendor'] if inv['vendor'] else ""
        date = inv['date'] if inv['date'] else ""
        amount = inv['amount'] if inv['amount'] else 0.0
        desc = inv['desc']
        create_receipt_image(inv['filename'], vendor, date, amount, desc)

# Create a README file with instructions for manual verification
with open('README.txt', 'w') as f:
    f.write('Generated invoice and receipt files for testing the invoice-organizer skill.\n')

