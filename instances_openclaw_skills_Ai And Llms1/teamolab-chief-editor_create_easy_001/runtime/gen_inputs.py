from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Deterministic input PDF with a marker phrase the evaluator can verify.
text_lines = [
    "Internal Announcement Draft",
    "Marker Phrase: ORANGE-OWL-2049",
    "Please improve clarity, grammar, and flow.",
    "Keep it short and professional.",
]

pdf_path = Path('announcement_draft.pdf')
c = canvas.Canvas(str(pdf_path), pagesize=letter)
width, height = letter
y = height - 72
for line in text_lines:
    c.drawString(72, y, line)
    y -= 18
c.save()
