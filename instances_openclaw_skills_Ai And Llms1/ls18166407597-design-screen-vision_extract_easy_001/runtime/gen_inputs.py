from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

Path('workspace').mkdir(exist_ok=True)
pdf_path = Path('workspace') / 'input.pdf'
marker = 'SCREEN_VISION_MARKER_4821'

c = canvas.Canvas(str(pdf_path), pagesize=letter)
width, height = letter
c.setFont('Helvetica', 14)
c.drawString(72, height - 72, 'Task document')
c.drawString(72, height - 100, f'Marker: {marker}')
c.drawString(72, height - 128, 'Please extract the marker text only.')
c.save()
