import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Create a simple test PDF with known content
def create_test_pdf():
    filename = 'sample_document.pdf'
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Add some test content
    c.drawString(100, height - 100, 'MARKER_TEXT: This is a test document')
    c.drawString(100, height - 130, 'Content: Sample PDF for text extraction testing')
    c.drawString(100, height - 160, 'Page: 1 of 1')
    c.drawString(100, height - 190, 'Keywords: pdf extraction python skill')
    
    c.save()
    print(f'Created {filename}')

if __name__ == '__main__':
    create_test_pdf()