from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

random.seed(1337)

w, h = 1200, 800
img = Image.new('RGB', (w, h), 'white')
d = ImageDraw.Draw(img)

# Simple UI mockup with deterministic marker content
panel = (120, 120, 1080, 620)
d.rounded_rectangle(panel, radius=24, fill=(245, 247, 250), outline=(200, 205, 210), width=3)

title = "Project Aurora"
status = "Status: Running"
metric_label = "Completion"
percentage = "78%"
marker = "VISION_MARKER_42"

# Use default font for portability
font = ImageFont.load_default()
large = ImageFont.load_default()

# Draw text at fixed positions
d.text((170, 175), title, fill=(20, 20, 20), font=large)
d.text((170, 240), status, fill=(60, 60, 60), font=font)
d.text((170, 320), metric_label, fill=(70, 70, 70), font=font)
d.text((420, 314), percentage, fill=(0, 102, 204), font=large)
d.text((170, 420), marker, fill=(120, 0, 120), font=font)

# Add a progress bar
bar_x1, bar_y1, bar_x2, bar_y2 = 170, 355, 940, 385
d.rounded_rectangle((bar_x1, bar_y1, bar_x2, bar_y2), radius=12, fill=(225, 229, 235), outline=(210, 215, 220))
filled = bar_x1 + int((bar_x2 - bar_x1) * 0.78)
d.rounded_rectangle((bar_x1, bar_y1, filled, bar_y2), radius=12, fill=(0, 122, 255))

# Save files
Path('input').mkdir(exist_ok=True)
img.save('input/screen.png')
Path('input/marker.txt').write_text(f'{marker}\nproject={title}\npercentage={percentage}\n', encoding='utf-8')
