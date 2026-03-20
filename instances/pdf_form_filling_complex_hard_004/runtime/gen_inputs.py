#!/usr/bin/env python3
import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from pypdf import PdfWriter
import random

# Set deterministic seed
random.seed(42)

# Create CSV with applicant data
applicant_data = {
    'first_name': ['JOHN'],
    'last_name': ['SMITH'],
    'ssn': ['123-45-6789'],
    'date_of_birth': ['01/15/1985'],
    'address': ['123 MAIN ST'],
    'city': ['ANYTOWN'],
    'state': ['CA'],
    'zip_code': ['90210'],
    'phone': ['555-0123'],
    'email': ['john.smith@email.com'],
    'income': ['75000'],
    'marital_status': ['SINGLE'],
    'dependents': ['0']
}

df = pd.DataFrame(applicant_data)
df.to_csv('applicant_data.csv', index=False)

# Create a complex form template with both fillable and non-fillable sections
def create_form_template():
    doc = SimpleDocTemplate('form_template.pdf', pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Page 1 - Personal Information
    story.append(Paragraph('GOVERNMENT APPLICATION FORM - MARKER_FORM_TITLE', styles['Title']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph('SECTION A: Personal Information', styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # Add form fields as text (simulating a scanned form)
    story.append(Paragraph('First Name: _____________________ Last Name: _____________________', styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Social Security Number: _____________________', styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Date of Birth: _____________________ Phone: _____________________', styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Address: _________________________________________________', styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('City: _____________ State: ____ ZIP: __________', styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Email: _________________________________________________', styles['Normal']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph('SECTION B: Financial Information - MARKER_SECTION_B', styles['Heading2']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Annual Income: $ _____________________', styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Marital Status: [ ] Single [ ] Married [ ] Divorced', styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Number of Dependents: _____________________', styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Page 2 - Certification
    story.append(Paragraph('PAGE 2: CERTIFICATION - MARKER_PAGE2', styles['Title']))
    story.append(Spacer(1, 20))
    story.append(Paragraph('I certify that the information provided is true and accurate.', styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Signature: ___________________________ Date: ___________', styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('FORM_MARKER_END', styles['Normal']))
    
    doc.build(story)

# Create supporting documents
def create_supporting_docs():
    # Document 1
    c = canvas.Canvas('doc1.pdf', pagesize=letter)
    c.drawString(100, 750, 'SUPPORTING DOCUMENT 1 - MARKER_DOC1')
    c.drawString(100, 700, 'This document contains additional information.')
    c.drawString(100, 650, 'Reference ID: SUP-001-2024')
    c.save()
    
    # Document 2
    c = canvas.Canvas('doc2.pdf', pagesize=letter)
    c.drawString(100, 750, 'SUPPORTING DOCUMENT 2 - MARKER_DOC2')
    c.drawString(100, 700, 'Additional verification document.')
    c.drawString(100, 650, 'Reference ID: SUP-002-2024')
    c.save()

create_form_template()
create_supporting_docs()

print('Generated input files: form_template.pdf, applicant_data.csv, doc1.pdf, doc2.pdf')