from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import json

base = Path('.')
(base / 'data').mkdir(exist_ok=True)

# Deterministic marker file
(base / 'data' / 'case_notes.txt').write_text(
    'MARKER_ALPHA\nIncident ID: 4821\nPriority: High\nRequested action: consolidate findings into a report.\n',
    encoding='utf-8'
)

# Deterministic JSON input
(base / 'data' / 'structured_input.json').write_text(
    json.dumps({
        'project': 'Orion',
        'markers': ['MARKER_BETA', 'MARKER_GAMMA'],
        'items': [
            {'name': 'thread-1', 'status': 'open', 'score': 7},
            {'name': 'thread-2', 'status': 'closed', 'score': 3}
        ]
    }, indent=2),
    encoding='utf-8'
)

# Deterministic PDF with embedded marker text
pdf_path = base / 'data' / 'reference_brief.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.setFont('Helvetica', 12)
c.drawString(72, 720, 'MARKER_PDF_DELTA')
c.drawString(72, 700, 'Reference brief for the adversarial analysis benchmark.')
c.drawString(72, 680, 'Key requirement: produce a markdown export with ranked options.')
c.showPage()
c.save()

# Manifest for evaluation
(base / 'data' / 'manifest.txt').write_text(
    'EXPECTED_MARKERS=MARKER_ALPHA,MARKER_BETA,MARKER_GAMMA,MARKER_PDF_DELTA\n',
    encoding='utf-8'
)
