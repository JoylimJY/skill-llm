import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path('.')
root.mkdir(parents=True, exist_ok=True)

# Deterministic text manifest with marker content
manifest = {
    'job_id': 'screen-vision-hard-042',
    'target_terms': ['Alpha Ledger', 'Beta Signal', 'Gamma Note'],
    'summary_hint': 'Recover the three marked phrases and report their approximate positions from the image.'
}
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

# Create a simple synthetic screenshot-like image with embedded markers
img = Image.new('RGB', (1400, 900), 'white')
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()

lines = [
    ('System Review Panel', (60, 50)),
    ('Alpha Ledger', (120, 180)),
    ('Beta Signal', (760, 360)),
    ('Gamma Note', (420, 700)),
    ('Status: ready for extraction', (60, 820)),
]
for text, pos in lines:
    draw.text(pos, text, fill='black', font=font)

# Mark approximate locations with colored boxes and coordinate labels
markers = [
    ('Alpha Ledger', (120, 180, 250, 205)),
    ('Beta Signal', (760, 360, 880, 385)),
    ('Gamma Note', (420, 700, 530, 725)),
]
for label, box in markers:
    draw.rectangle(box, outline='red', width=2)

img.save(root / 'screen_capture.png')

# Ground truth coordinate map for evaluation reference (not necessarily visible to the solver)
truth = {
    'Alpha Ledger': {'x': 185, 'y': 192},
    'Beta Signal': {'x': 820, 'y': 372},
    'Gamma Note': {'x': 475, 'y': 712},
}
(root / 'truth.json').write_text(json.dumps(truth, indent=2), encoding='utf-8')
