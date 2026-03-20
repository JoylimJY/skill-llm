import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from pypdf import PdfWriter

def create_quarterly_report(filename, quarter, year, pages=3):
    """Create a quarterly report PDF with specific marker content"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Page 1 - Executive Summary (marker content)
    title = f"Q{quarter} {year} Executive Summary"
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 12))
    
    exec_summary = f"EXEC_SUMMARY_MARKER_Q{quarter}: This quarter showed significant growth in our core business segments. Revenue increased by {quarter * 5}% compared to the previous quarter. Key achievements include strategic partnerships and operational efficiency improvements."
    story.append(Paragraph(exec_summary, styles['Normal']))
    story.append(Spacer(1, 24))
    
    # Add more pages with different content
    for page_num in range(2, pages + 1):
        story.append(Paragraph(f"Page {page_num} - Detailed Analysis", styles['Heading1']))
        story.append(Spacer(1, 12))
        content = f"CONTENT_PAGE_{page_num}_Q{quarter}: Detailed financial analysis and operational metrics for quarter {quarter} of {year}. This section contains comprehensive data about performance indicators and market trends."
        story.append(Paragraph(content, styles['Normal']))
        story.append(Spacer(1, 12))
    
    doc.build(story)
    
    # Add metadata to the PDF
    from pypdf import PdfWriter, PdfReader
    reader = PdfReader(filename)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
    
    # Set metadata with marker content
    metadata = {
        '/Title': f'TITLE_MARKER: Q{quarter} {year} Quarterly Report',
        '/Author': 'Corporate Finance Team',
        '/Subject': f'Financial Report for Quarter {quarter}'
    }
    writer.add_metadata(metadata)
    
    with open(filename, 'wb') as output_file:
        writer.write(output_file)

# Create reports directory
os.makedirs('reports', exist_ok=True)

# Generate three quarterly reports with deterministic content
create_quarterly_report('reports/Q1_2023.pdf', 1, 2023, 4)
create_quarterly_report('reports/Q2_2023.pdf', 2, 2023, 3)
create_quarterly_report('reports/Q3_2023.pdf', 3, 2023, 5)

print('Generated quarterly report PDFs with marker content')