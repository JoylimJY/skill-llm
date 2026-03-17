import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

np.random.seed(42)

def create_financial_pdf():
    doc = SimpleDocTemplate("financial_data.pdf", pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("QUARTERLY FINANCIAL REPORT 2023", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Revenue table (marker: REVENUE_TABLE_MARKER)
    revenue_header = Paragraph("Revenue by Quarter (REVENUE_TABLE_MARKER)", styles['Heading2'])
    elements.append(revenue_header)
    elements.append(Spacer(1, 10))
    
    revenue_data = [
        ['Quarter', 'Product A', 'Product B', 'Product C', 'Total'],
        ['Q1 2023', '125000', '87500', '112000', '324500'],
        ['Q2 2023', '134000', '92300', '118500', '344800'],
        ['Q3 2023', '142500', '98700', '125000', '366200'],
        ['Q4 2023', '151000', '105200', '131500', '387700']
    ]
    
    revenue_table = Table(revenue_data)
    revenue_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(revenue_table)
    elements.append(Spacer(1, 30))
    
    # Expense table (marker: EXPENSE_TABLE_MARKER)
    expense_header = Paragraph("Operating Expenses by Department (EXPENSE_TABLE_MARKER)", styles['Heading2'])
    elements.append(expense_header)
    elements.append(Spacer(1, 10))
    
    expense_data = [
        ['Department', 'Q1', 'Q2', 'Q3', 'Q4'],
        ['Marketing', '45000', '47500', '52000', '54500'],
        ['R&D', '67500', '71000', '73500', '76000'],
        ['Operations', '89000', '92500', '96000', '98500'],
        ['Admin', '23500', '24000', '25500', '26000']
    ]
    
    expense_table = Table(expense_data)
    expense_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(expense_table)
    elements.append(Spacer(1, 30))
    
    # Profit margin table (marker: MARGIN_TABLE_MARKER)
    margin_header = Paragraph("Profit Margins by Region (MARGIN_TABLE_MARKER)", styles['Heading2'])
    elements.append(margin_header)
    elements.append(Spacer(1, 10))
    
    margin_data = [
        ['Region', 'Revenue', 'Cost', 'Margin %'],
        ['North America', '542000', '380000', '29.9'],
        ['Europe', '387000', '289000', '25.3'],
        ['Asia Pacific', '234000', '175000', '25.2'],
        ['Latin America', '159000', '128000', '19.5']
    ]
    
    margin_table = Table(margin_data)
    margin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(margin_table)
    
    doc.build(elements)
    print("Generated financial_data.pdf with three tables containing marker content")

if __name__ == "__main__":
    create_financial_pdf()