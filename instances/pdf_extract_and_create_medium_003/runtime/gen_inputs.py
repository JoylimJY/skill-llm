import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import random

# Set deterministic seed
random.seed(42)

# Create sample financial data
companies = ['ACME Corp', 'Beta Ltd', 'Gamma Inc', 'Delta Co']
quarters = ['Q1 2023', 'Q2 2023', 'Q3 2023', 'Q4 2023']

# Generate deterministic financial data with marker values
financial_data = []
for i, company in enumerate(companies):
    for j, quarter in enumerate(quarters):
        revenue = 1000000 + (i * 100000) + (j * 50000) + 12345  # Marker: 12345
        expenses = int(revenue * 0.7) + 6789  # Marker: 6789
        profit = revenue - expenses
        financial_data.append([company, quarter, f'${revenue:,}', f'${expenses:,}', f'${profit:,}'])

# Create PDF with tables
doc = SimpleDocTemplate('financial_report.pdf', pagesize=letter)
elements = []
styles = getSampleStyleSheet()

# Title
title = Paragraph('Company Financial Data', styles['Title'])
elements.append(title)
elements.append(Spacer(1, 20))

# First table - Revenue data
revenue_data = [['Company', 'Quarter', 'Revenue']]
for row in financial_data[:8]:  # First 8 rows
    revenue_data.append([row[0], row[1], row[2]])

table1 = Table(revenue_data)
table1.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))

elements.append(table1)
elements.append(Spacer(1, 30))

# Second table - Expenses data
expenses_data = [['Company', 'Quarter', 'Expenses']]
for row in financial_data[8:]:  # Remaining rows
    expenses_data.append([row[0], row[1], row[3]])

table2 = Table(expenses_data)
table2.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))

elements.append(table2)

# Build the PDF
doc.build(elements)
print('Created financial_report.pdf with financial data tables')