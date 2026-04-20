from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Deterministic inputs with embedded markers
text_file = Path('screen_log.txt')
text_file.write_text(
    'System status: READY\n'
    'Marker: OCR_TARGET_ALPHA\n'
    'Coordinates hint: X=184 Y=72\n'
    'Footer: end of log\n',
    encoding='utf-8'
)

img = Image.new('RGB', (640, 240), color='white')
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()
draw.text((40, 50), 'Please locate this text:', fill='black', font=font)
draw.text((40, 90), 'OCR_TARGET_ALPHA', fill='black', font=font)
draw.text((40, 130), 'X: 184   Y: 72', fill='black', font=font)
img.save('screen_capture.png')
