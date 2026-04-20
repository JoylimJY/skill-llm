import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

root = Path('.')
# Deterministic marker file
(root / 'project_seed.txt').write_text('ATLAS-MARKER-7F3\nproject=Atlas Migration\nseed=1337\n', encoding='utf-8')

# Deterministic reference PDF with known marker content
pdf_path = root / 'reference_brief.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
text = c.beginText(72, 720)
lines = [
    'Atlas Migration Brief',
    'Marker: ATLAS-MARKER-7F3',
    'Roles: Lead, Engineer, Maintainer',
    'Weekly focus: TASK.md, CHANGELOG.md, CONTEXT.md, WEEKLY-REPORT.md',
    'Repeated operation: update TASK and append CHANGELOG',
]
for line in lines:
    text.textLine(line)
c.drawText(text)
c.showPage()
c.save()

# Input hint file for task realism
(root / 'handoff_notes.txt').write_text(
    'Create collaboration docs for Atlas Migration using the Agent Sync workflow.\n'
    'Ensure qmd retrieval is mentioned in CONTEXT and a pattern discovery section exists.\n',
    encoding='utf-8'
)
