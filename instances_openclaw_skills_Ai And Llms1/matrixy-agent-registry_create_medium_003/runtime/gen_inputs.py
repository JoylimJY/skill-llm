from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

base = Path('.')
(base / 'notes').mkdir(exist_ok=True)

(base / 'notes' / 'README.txt').write_text(
    'AGENT-REGISTRY TASK MARKER\n'
    'This workspace contains a sample registry migration scenario.\n'
    'Marker ID: AR-2025-04-17\n',
    encoding='utf-8'
)

(base / 'manifest.json').write_text(
    '{"project":"agent-registry","marker":"AR-2025-04-17","version":"2.0.1"}\n',
    encoding='utf-8'
)

pdf_path = base / 'notes' / 'source.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.drawString(72, 720, 'Agent Registry Evaluation Source')
c.drawString(72, 700, 'Marker ID: AR-2025-04-17')
c.drawString(72, 680, 'Expected output should reference a security-auditor style agent.')
c.showPage()
c.save()
