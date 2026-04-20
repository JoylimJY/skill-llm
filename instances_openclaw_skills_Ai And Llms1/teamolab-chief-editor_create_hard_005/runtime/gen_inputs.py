import json
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

SEED_MARKER = "KB-MARKER-ALPHA-4931"

base = Path('.')
base.mkdir(parents=True, exist_ok=True)

# Markdown dossier
(base / 'dossier.md').write_text(
    '# Internal Editorial Dossier\n\n'
    f'Marker: {SEED_MARKER}\n\n'
    'Source A: The company launched Project Aurora in Q2 2024.\n'
    'Source B: The preferred headline is "Aurora Launch Report: Editorial Review".\n'
    'Source C: Evaluation criteria must be included as a standalone section.\n'
    'Source D: The references section must appear at the very end of the article.\n'
    'Source E: Relevant URL: https://example.com/editorial-standards\n',
    encoding='utf-8'
)

# Draft article with issues
(base / 'draft_article.txt').write_text(
    'Headline options:\n'
    '1. Aurora Launch Report\n'
    '2. Internal Launch Summary\n\n'
    'Draft body:\n'
    'Project Aurora was launched in 2023, according to the draft.\n'
    'The article mentions criteria but does not present them as a section.\n\n'
    'References\n'
    '- https://example.com/old-reference\n',
    encoding='utf-8'
)

# A small PDF containing a URL and marker content
pdf_path = base / 'attached_notes.pdf'
cnv = canvas.Canvas(str(pdf_path), pagesize=letter)
cnv.setFont('Helvetica', 12)
cnv.drawString(72, 720, f'Confidential notes {SEED_MARKER}')
cnv.drawString(72, 700, 'Please review https://example.com/editorial-standards')
cnv.drawString(72, 680, 'Project Aurora launched in Q2 2024.')
cnv.showPage()
cnv.save()

# Metadata for convenience
(base / 'input_manifest.json').write_text(
    json.dumps({
        'seed_marker': SEED_MARKER,
        'files': ['dossier.md', 'draft_article.txt', 'attached_notes.pdf']
    }, indent=2),
    encoding='utf-8'
)
