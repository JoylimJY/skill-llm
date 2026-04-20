from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, random

random.seed(1337)
base = Path('.')
base.mkdir(parents=True, exist_ok=True)

# Create a deterministic synthetic screenshot-like image with marker text.
img = Image.new('RGB', (1200, 800), 'white')
draw = ImageDraw.Draw(img)

# Use a default font available in PIL.
try:
    font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 36)
    font_med = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
except Exception:
    font_big = ImageFont.load_default()
    font_med = ImageFont.load_default()

texts = [
    ('Finance Dashboard', (60, 40), font_big),
    ('Available Balance: 1284.50 USD', (60, 140), font_med),
    ('Unread Alerts: 7', (60, 200), font_med),
    ('Sync Status: Completed', (60, 260), font_med),
    ('MarkerID: SCREENVISION-ALPHA-42', (60, 340), font_med),
]
for text, pos, font in texts:
    draw.text(pos, text, fill='black', font=font)

# Add a small metadata file with markers for evaluation.
meta = {
    'expected_title': 'Finance Dashboard',
    'expected_balance': '1284.50',
    'expected_alerts': '7',
    'marker': 'SCREENVISION-ALPHA-42'
}
(base / 'ground_truth.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
img.save(base / 'screenshot.png')
