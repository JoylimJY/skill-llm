from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import json
import random

random.seed(1337)

# Marker file for deterministic verification
Path('task_markers.json').write_text(json.dumps({
    'marker_id': 'clawd-blue-hat-arms-001',
    'theme': 'ocean_blue',
    'variants': ['with_arms', 'with_hat', 'loading_screen'],
    'required_body_rgb': 'rgb(100,149,237)',
    'required_body_ansi': 'ansi:blueBright'
}, indent=2))

# Create a small reference PDF with embedded markers for potential downstream use
pdf_path = Path('reference_brief.pdf')
c = canvas.Canvas(str(pdf_path), pagesize=letter)
width, height = letter
c.setFont('Helvetica', 12)
lines = [
    'Clawd customization brief',
    'Marker: clawd-blue-hat-arms-001',
    'Theme: ocean_blue',
    'Requirements:',
    '- Add both arms',
    '- Add a top hat',
    '- Change body color to RGB 100,149,237',
    '- Change ANSI fallback to ansi:blueBright',
    '- Update both prompt and loading-screen art',
]
text_y = height - 1 * inch
for line in lines:
    c.drawString(1 * inch, text_y, line)
    text_y -= 0.3 * inch
c.showPage()
c.save()

# Deterministic manifest of generated assets
Path('gen_manifest.txt').write_text('\n'.join([
    'task_markers.json',
    'reference_brief.pdf',
    'marker_id=clawd-blue-hat-arms-001'
]))
