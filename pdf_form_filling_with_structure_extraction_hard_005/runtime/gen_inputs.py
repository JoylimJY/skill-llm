#!/usr/bin/env python3
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

width, height = letter

c = canvas.Canvas('form.pdf', pagesize=letter)

# Draw form structure with labels and entry areas
c.setFont('Helvetica', 12)

# Last Name field
c.drawString(50, height - 100, 'Last Name:')
c.rect(150, height - 110, 200, 20, stroke=1, fill=0)

# First Name field
c.drawString(50, height - 150, 'First Name:')
c.rect(150, height - 160, 200, 20, stroke=1, fill=0)

# Age field
c.drawString(50, height - 200, 'Age:')
c.rect(150, height - 210, 100, 20, stroke=1, fill=0)

# US Citizen checkbox
c.drawString(50, height - 250, 'US Citizen:')
c.rect(150, height - 260, 15, 15, stroke=1, fill=0)

# Employment Status
c.drawString(50, height - 300, 'Employment Status:')
c.drawString(150, height - 300, '[ ] Employed')
c.drawString(150, height - 320, '[ ] Unemployed')
c.drawString(150, height - 340, '[ ] Student')

# Draw checkboxes for employment status
c.rect(145, height - 305, 10, 10, stroke=1, fill=0)
c.rect(145, height - 325, 10, 10, stroke=1, fill=0)
c.rect(145, height - 345, 10, 10, stroke=1, fill=0)

c.save()

print('form.pdf created successfully')
