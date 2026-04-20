from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

base = Path('.')

# Marker file for deterministic verification
(base / 'task_marker.txt').write_text(
    'MARKER: ADV_PROMPTING_MEDIUM_2025\nCASE: consolidation-debugging\nSEED: 1337\n',
    encoding='utf-8'
)

# Deterministic PDF with embedded marker text
pdf_path = base / 'reference_brief.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
y = 750
lines = [
    'Reference Brief',
    'MARKER: ADV_PROMPTING_MEDIUM_2025',
    'The system has two proposed fixes for a broken analysis workflow.',
    'Fix A improves export reliability but may hide failure details.',
    'Fix B improves grading strictness but may overfit to one filename.',
    'The desired task asks for adversarial analysis, validation, and consolidation.',
]
for line in lines:
    c.drawString(72, y, line)
    y -= 18
c.showPage()
c.save()

# Input notes in a simple text file
(base / 'user_request.txt').write_text(
    'Please analyze the two proposed fixes, identify weaknesses, validate mitigations, and recommend the best path forward.\n',
    encoding='utf-8'
)
