from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def create_test_pdf(filename, title, content):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, title)
    c.setFont("Helvetica", 12)
    y_pos = height - 100
    for line in content.split('\n'):
        c.drawString(50, y_pos, line)
        y_pos -= 20
    c.save()

content1 = "MARKER_REPORT_2023\nThis is the 2023 annual report.\nPage 1 of merged document."
content2 = "MARKER_REPORT_2024\nThis is the 2024 annual report.\nPage 2 of merged document."
content3 = "MARKER_APPENDIX\nThis is the appendix section.\nPage 3 of merged document."

create_test_pdf('report_2023.pdf', '2023 Report', content1)
create_test_pdf('report_2024.pdf', '2024 Report', content2)
create_test_pdf('appendix.pdf', 'Appendix', content3)

print('Input PDFs created successfully')