from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Deterministic input generation with embedded markers
notes = Path('notes.txt')
notes.write_text(
    'SMART CONTEXT BRIEF\n'
    'Marker Alpha: READ_ONLY_IF_NEEDED\n'
    'Marker Beta: BATCH_INDEPENDENT_CALLS\n'
    'Marker Gamma: NO_REDUNDANT_READING\n'
    'Keep responses short for simple tasks and structured for complex ones.\n'
    'Avoid unnecessary tool calls and avoid re-reading files already in context.\n',
    encoding='utf-8'
)

pdf_path = Path('reference.pdf')
cnv = canvas.Canvas(str(pdf_path), pagesize=letter)
cnv.setTitle('Smart Context Reference')
cnv.drawString(72, 720, 'Smart Context Reference')
cnv.drawString(72, 700, 'Marker Delta: COST_AWARE_AGENT')
cnv.drawString(72, 680, 'Marker Epsilon: SKIP_NARRATION')
cnv.drawString(72, 660, 'Use context already available before reaching for tools.')
cnv.save()
