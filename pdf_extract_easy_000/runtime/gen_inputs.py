import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

os.makedirs('inputs', exist_ok=True)

c = canvas.Canvas('inputs/report.pdf', pagesize=letter)
width, height = letter

# Page 1
c.drawString(100, height - 100, 'MARKER_PAGE_1_START')
c.drawString(100, height - 120, 'This is the first page of the report.')
c.drawString(100, height - 140, 'It contains important information.')
c.drawString(100, height - 160, 'MARKER_PAGE_1_END')
c.showPage()

# Page 2
c.drawString(100, height - 100, 'MARKER_PAGE_2_START')
c.drawString(100, height - 120, 'This is the second page of the report.')
c.drawString(100, height - 140, 'It has more content here.')
c.drawString(100, height - 160, 'MARKER_PAGE_2_END')
c.showPage()

# Page 3
c.drawString(100, height - 100, 'MARKER_PAGE_3_START')
c.drawString(100, height - 120, 'This is the third and final page.')
c.drawString(100, height - 140, 'The report ends here.')
c.drawString(100, height - 160, 'MARKER_PAGE_3_END')
c.showPage()

c.save()
print('Generated report.pdf with 3 pages')