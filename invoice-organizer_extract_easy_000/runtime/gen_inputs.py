import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image, ImageDraw, ImageFont

# Create two PDF invoices and one JPG receipt with known information

def create_pdf_invoice(filename, vendor, invoice_num, date_str, amount, description):
    c = canvas.Canvas(filename, pagesize=letter)
    text = c.beginText(40, 700)
    text.setFont("Helvetica", 12)
    text.textLine(vendor)
    text.textLine(f"Invoice #: {invoice_num}")
    text.textLine(f"Invoice Date: {date_str}")
    text.textLine(f"Amount Due: ${amount:.2f}")
    text.textLine(f"Description: {description}")
    c.drawText(text)
    c.save()


def create_jpg_receipt(filename, vendor, date_str, amount, description):
    # Create a white image
    img = Image.new('RGB', (400, 200), color='white')
    d = ImageDraw.Draw(img)
    # Use default font
    d.text((10, 10), f"{vendor}\nDate: {date_str}\nTotal: ${amount:.2f}\nItem: {description}", fill='black')
    img.save(filename)


def main():
    # Fixed dates
    date1 = "2024-03-15"
    date2 = "2024-02-10"
    date3 = "2024-01-20"

    # Make input folder
    os.makedirs(".", exist_ok=True)

    # Create PDF invoice 1
    create_pdf_invoice(
        "invoice1.pdf",
        "Adobe",
        "INV-12345",
        date1,
        52.99,
        "Creative Cloud Subscription"
    )

    # Create PDF invoice 2
    create_pdf_invoice(
        "amazon_invoice.pdf",
        "Amazon",
        "123-4567890-1234567",
        date3,
        127.45,
        "Office Supplies"
    )

    # Create JPG receipt
    create_jpg_receipt(
        "receipt1.jpg",
        "Staples",
        date2,
        34.15,
        "Printer Paper"
    )

if __name__ == "__main__":
    main()
