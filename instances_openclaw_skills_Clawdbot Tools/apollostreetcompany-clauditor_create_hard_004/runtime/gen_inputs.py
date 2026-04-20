from pathlib import Path
import json
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont
import pandas as pd

random.seed(1337)
base = Path('.')
base.mkdir(exist_ok=True)

# Deterministic text fixture with embedded markers
(base / 'install_notes.txt').write_text(
    'CLAUDITOR_MARKER_ALPHA\n'
    'This workspace contains a guided install scenario for clauditor.\n'
    'CLAUDITOR_MARKER_BETA\n'
    'The expected output should preserve the audit trail markers.\n',
    encoding='utf-8'
)

# CSV fixture with markers
rows = [
    {'step': 1, 'name': 'create-user', 'marker': 'CSV_MARKER_X'},
    {'step': 2, 'name': 'configure-paths', 'marker': 'CSV_MARKER_Y'},
    {'step': 3, 'name': 'verify-status', 'marker': 'CSV_MARKER_Z'},
]
pd.DataFrame(rows).to_csv(base / 'workflow.csv', index=False)

# JSON fixture with markers
json.dump(
    {
        'task': 'clauditor-install',
        'markers': ['JSON_MARKER_A', 'JSON_MARKER_B'],
        'meta': {'difficulty': 'hard', 'seed': 1337},
    },
    (base / 'task_data.json').open('w', encoding='utf-8'),
    indent=2,
)

# Image fixture with visible marker text
img = Image.new('RGB', (800, 240), color='white')
draw = ImageDraw.Draw(img)
draw.text((20, 20), 'IMG_MARKER_1', fill='black')
draw.text((20, 80), 'IMG_MARKER_2', fill='black')
draw.text((20, 140), 'Claudit0r guided audit workspace', fill='black')
img.save(base / 'reference.png')

# PDF fixture with embedded marker content
pdf_path = base / 'reference.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.drawString(72, 720, 'PDF_MARKER_ONE')
c.drawString(72, 700, 'PDF_MARKER_TWO')
c.drawString(72, 680, 'Clauditor installation reference document')
c.showPage()
c.save()

# Manifest for easy inspection
manifest = {
    'files': [
        'install_notes.txt',
        'workflow.csv',
        'task_data.json',
        'reference.png',
        'reference.pdf',
    ],
    'required_markers': [
        'CLAUDITOR_MARKER_ALPHA',
        'CLAUDITOR_MARKER_BETA',
        'CSV_MARKER_X',
        'JSON_MARKER_A',
        'IMG_MARKER_1',
        'PDF_MARKER_ONE',
    ],
}
(base / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
