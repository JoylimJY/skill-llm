#!/usr/bin/env python3
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

width, height = letter

c = canvas.Canvas('form.pdf', pagesize=letter)

# Draw form structure with labels and entry areas
# Last Name
c.drawString(50, height - 100, 'Last Name:')
c.rect(150, height - 110, 200, 20, stroke=1, fill=0)

# First Name
c.drawString(50, height - 150, 'First Name:')
c.rect(150, height - 160, 200, 20, stroke=1, fill=0)

# Age
c.drawString(50, height - 200, 'Age:')
c.rect(150, height - 210, 100, 20, stroke=1, fill=0)

# US Citizen checkbox
c.drawString(50, height - 250, 'US Citizen:')
c.rect(150, height - 260, 15, 15, stroke=1, fill=0)

# Employment Status
c.drawString(50, height - 310, 'Employment Status:')
c.drawString(150, height - 310, '[ ] Employed')
c.drawString(150, height - 330, '[ ] Unemployed')
c.drawString(150, height - 350, '[ ] Student')

# Add checkboxes for employment status
c.rect(155, height - 315, 10, 10, stroke=1, fill=0)
c.rect(155, height - 335, 10, 10, stroke=1, fill=0)
c.rect(155, height - 355, 10, 10, stroke=1, fill=0)

c.save()

# Create expected structure output
structure = {
    'labels': [
        {'text': 'Last Name:', 'x0': 50, 'top': height - 105, 'x1': 140, 'bottom': height - 95},
        {'text': 'First Name:', 'x0': 50, 'top': height - 155, 'x1': 140, 'bottom': height - 145},
        {'text': 'Age:', 'x0': 50, 'top': height - 205, 'x1': 140, 'bottom': height - 195},
        {'text': 'US Citizen:', 'x0': 50, 'top': height - 255, 'x1': 140, 'bottom': height - 245},
        {'text': 'Employment Status:', 'x0': 50, 'top': height - 315, 'x1': 200, 'bottom': height - 305}
    ],
    'checkboxes': [
        {'x0': 150, 'top': height - 260, 'x1': 165, 'bottom': height - 245, 'label': 'US Citizen'},
        {'x0': 155, 'top': height - 315, 'x1': 165, 'bottom': height - 305, 'label': 'Employed'},
        {'x0': 155, 'top': height - 335, 'x1': 165, 'bottom': height - 325, 'label': 'Unemployed'},
        {'x0': 155, 'top': height - 355, 'x1': 165, 'bottom': height - 345, 'label': 'Student'}
    ],
    'lines': [
        {'x0': 150, 'y': height - 110, 'x1': 350, 'y': height - 110},
        {'x0': 150, 'y': height - 160, 'x1': 350, 'y': height - 160},
        {'x0': 150, 'y': height - 210, 'x1': 250, 'y': height - 210}
    ]
}

with open('form_structure.json', 'w') as f:
    json.dump(structure, f, indent=2)

print('Generated form.pdf and form_structure.json')
