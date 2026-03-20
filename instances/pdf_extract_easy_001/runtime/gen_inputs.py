#!/usr/bin/env python3
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Set seed for deterministic output
random.seed(42)

def create_sales_report():
    doc = SimpleDocTemplate("sales_report.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add title with marker content
    title = Paragraph("MARKER_TITLE: Sales Report Q4 2023", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Add introduction with marker
    intro = Paragraph("MARKER_INTRO: This report contains sales data for the fourth quarter of 2023. The data shows performance across different regions and product categories.", styles['Normal'])
    story.append(intro)
    story.append(Spacer(1, 12))
    
    # Add sales table with marker data
    table_data = [
        ['Region', 'Product', 'Units Sold', 'Revenue'],
        ['North', 'Widget A', '150', '$15,000'],
        ['South', 'Widget B', '225', '$22,500'],
        ['East', 'Widget C', '180', '$18,000'],
        ['West', 'MARKER_PRODUCT: Special Item', '95', '$9,500']
    ]
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 12))
    
    # Add conclusion with marker
    conclusion = Paragraph("MARKER_CONCLUSION: Total revenue for Q4 was $65,000 across all regions. This represents a 12% increase from the previous quarter.", styles['Normal'])
    story.append(conclusion)
    
    doc.build(story)
    print("Created sales_report.pdf with marker content")

if __name__ == "__main__":
    create_sales_report()