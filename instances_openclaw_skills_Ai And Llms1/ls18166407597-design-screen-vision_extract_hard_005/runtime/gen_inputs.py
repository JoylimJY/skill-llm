from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, random

random.seed(1337)
base = Path('.')
# Create a deterministic synthetic screenshot-like image with embedded markers
img = Image.new('RGB', (1280, 720), 'white')
d = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28)
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
except Exception:
    font = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Marker content for eval verification
texts = [
    ('CONFIRM DELETE', (120, 110)),
    ('File: report_q4_final.pdf', (120, 170)),
    ('This action cannot be undone', (120, 230)),
    ('取消', (980, 560)),
    ('Confirm', (1100, 560)),
    ('Primary Code: ZX-2048', (120, 320)),
]
for t, pos in texts:
    d.text(pos, t, fill='black', font=font if len(t) < 20 else font_small)

# Add a few distractors
for i, (t, pos) in enumerate([('Notes', (900, 80)), ('Draft', (900, 130)), ('Sync complete', (900, 180))]):
    d.text(pos, t, fill=(60, 60, 60), font=font_small)

img_path = base / 'screen_capture.png'
img.save(img_path)

metadata = {
    'image': 'screen_capture.png',
    'expected_markers': [
        {'text': 'CONFIRM DELETE', 'x': 120, 'y': 110},
        {'text': 'File: report_q4_final.pdf', 'x': 120, 'y': 170},
        {'text': 'This action cannot be undone', 'x': 120, 'y': 230},
        {'text': '取消', 'x': 980, 'y': 560},
        {'text': 'Confirm', 'x': 1100, 'y': 560},
        {'text': 'Primary Code: ZX-2048', 'x': 120, 'y': 320},
    ]
}
(base / 'input_manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
