import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

base = Path('.')
(base / 'source').mkdir(exist_ok=True)
(base / 'deliverable').mkdir(exist_ok=True)

# Marker-rich text inputs
(base / 'source' / 'project_brief.txt').write_text(
    'PROJECT_MARKER: ORION-47\n'
    'The Orion toolkit helps teams package internal docs quickly.\n'
    'Primary script: run_orion.py\n'
    'Release cadence: weekly\n',
    encoding='utf-8'
)

(base / 'source' / 'file_index.txt').write_text(
    'FILES:\n'
    '- run_orion.py\n'
    '- config.yaml\n'
    '- sample_output.txt\n'
    'INDEX_MARKER: IDX-9031\n',
    encoding='utf-8'
)

# JSON metadata input
metadata = {
    'marker': 'META-5520',
    'project': 'Orion Toolkit',
    'owner': 'Docs Team',
    'main_script': 'run_orion.py',
    'run_command': 'python run_orion.py --help'
}
(base / 'source' / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')

# Deterministic PDF with embedded marker text
pdf_path = base / 'source' / 'spec.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.setTitle('Orion Spec')
c.drawString(72, 720, 'ORION SPEC SHEET')
c.drawString(72, 700, 'PDF_MARKER: PDF-1188')
c.drawString(72, 680, 'Main script: run_orion.py')
c.drawString(72, 660, 'Notes: include quick start and changelog')
c.showPage()
c.save()

# Tiny helper file for realism
(base / 'source' / 'sample_output.txt').write_text(
    'Sample output for verification.\nOUTPUT_MARKER: OUT-7712\n',
    encoding='utf-8'
)
