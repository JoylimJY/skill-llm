from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Deterministic input with embedded markers for evaluation
root = Path('.')
text = (
    'MARKER_TALK_TOPIC: bootstrap-observability\n'
    'MARKER_CORE_INSIGHT: learn normal before enforcing alerts\n'
    'MARKER_EXAMPLE: reproduce-to-debug was the pain point\n'
    'MARKER_AUDIENCE: engineers shipping new systems\n'
)
(root / 'input_notes.txt').write_text(text, encoding='utf-8')

pdf_path = root / 'context.pdf'
cnv = canvas.Canvas(str(pdf_path), pagesize=letter)
cnv.setFont('Helvetica', 12)
lines = [
    'Technical insight notes',
    'MARKER_TALK_TOPIC: bootstrap-observability',
    'MARKER_CORE_INSIGHT: learn normal before enforcing alerts',
    'MARKER_EXAMPLE: reproduce-to-debug was the pain point',
    'MARKER_AUDIENCE: engineers shipping new systems',
]
y = 750
for line in lines:
    cnv.drawString(72, y, line)
    y -= 20
cnv.showPage()
cnv.save()
