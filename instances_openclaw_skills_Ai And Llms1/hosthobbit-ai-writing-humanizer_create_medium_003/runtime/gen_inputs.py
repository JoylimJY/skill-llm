from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import random

random.seed(1337)
base = Path('.')

text = (
    'At the end of the day, the process was simple, but it is important to remember that '
    'the first draft was full of stock transitions. Firstly, the message should sound natural. '
    'Secondly, it should avoid obvious patterns, and finally, it should read like something a person would actually send. '
    'I hope this helps, and let me know if you have any questions. '\
    'The update has been reviewed, and the summary was prepared with care. '
    'It is worth noting that the language has been adjusted to sound less mechanical.'
)
(base / 'draft.txt').write_text(text, encoding='utf-8')

marker = 'MARKER-7F3A-HUMANIZE-OK'
(base / 'marker.txt').write_text(marker + '\n', encoding='utf-8')

pdf_path = base / 'reference.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
width, height = letter
c.setFont('Helvetica', 11)
lines = [
    'Reference notes for the task:',
    marker,
    'This page is intentionally simple and deterministic.',
    'The cleaned output should preserve meaning while removing AI-like phrasing.'
]
y = height - 72
for line in lines:
    c.drawString(72, y, line)
    y -= 18
c.showPage()
c.save()
