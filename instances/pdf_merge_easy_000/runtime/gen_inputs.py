#!/usr/bin/env python3
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_test_pdf(filename, title, content_lines):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont('Helvetica-Bold', 16)
    c.drawString(100, height - 100, title)
    
    # Content lines
    c.setFont('Helvetica', 12)
    y_pos = height - 150
    for line in content_lines:
        c.drawString(100, y_pos, line)
        y_pos -= 20
    
    c.save()

# Create three test PDFs with specific marker content
create_test_pdf('doc1.pdf', 'Document One', [
    'This is the first document.',
    'Marker: DOC1_CONTENT_MARKER',
    'Page count: 1'
])

create_test_pdf('doc2.pdf', 'Document Two', [
    'This is the second document.',
    'Marker: DOC2_CONTENT_MARKER', 
    'Contains important data.',
    'Page count: 1'
])

create_test_pdf('doc3.pdf', 'Document Three', [
    'This is the third document.',
    'Marker: DOC3_CONTENT_MARKER',
    'Final document in series.',
    'Page count: 1'
])

print('Created test PDF files: doc1.pdf, doc2.pdf, doc3.pdf')