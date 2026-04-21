muimport os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Create deterministic blurry screenshots
np.random.seed(42)

# Generate screenshot 1 - UI mockup
img1 = Image.new('RGB', (800, 600), color=(240, 240, 240))
draw = ImageDraw.Draw(img1)

# Add UI elements
draw.rectangle([50, 50, 750, 100], fill=(70, 130, 180), outline=(0, 0, 0))
draw.text((60, 65), 'Application Header', fill=(255, 255, 255))
draw.rectangle([50, 120, 750, 550], fill=(255, 255, 255), outline=(0, 0, 0))
draw.text((60, 140), 'MARKER_UI_CONTENT: Main content area with important text', fill=(0, 0, 0))
draw.text((60, 180), 'This is a sample screenshot for enhancement testing', fill=(100, 100, 100))

# Add blur by resizing down and up
img1_small = img1.resize((200, 150), Image.LANCZOS)
img1_blurry = img1_small.resize((800, 600), Image.LANCZOS)
img1_blurry.save('screenshot1.png')

# Generate screenshot 2 - code editor mockup
img2 = Image.new('RGB', (1024, 768), color=(30, 30, 30))
draw2 = ImageDraw.Draw(img2)

# Dark theme code editor
draw2.rectangle([0, 0, 1024, 40], fill=(50, 50, 50))
draw2.text((10, 15), 'code_editor.py - Enhanced', fill=(200, 200, 200))
draw2.text((50, 80), 'MARKER_CODE_CONTENT: def enhance_image(input_path):', fill=(86, 156, 214))
draw2.text((70, 110), 'return processed_image', fill=(156, 220, 254))
draw2.text((50, 140), '# This function improves image quality', fill=(106, 153, 85))

# Add more blur to this one
img2_small = img2.resize((256, 192), Image.LANCZOS)
img2_blurry = img2_small.resize((1024, 768), Image.LANCZOS)
img2_blurry.save('documentation_screenshot.png')

# Generate screenshot 3 - web interface
img3 = Image.new('RGB', (1200, 900), color=(248, 249, 250))
draw3 = ImageDraw.Draw(img3)

# Web interface mockup
draw3.rectangle([0, 0, 1200, 80], fill=(0, 123, 255))
draw3.text((20, 30), 'MARKER_WEB_CONTENT: Image Enhancement Dashboard', fill=(255, 255, 255))
draw3.rectangle([100, 150, 1100, 800], fill=(255, 255, 255), outline=(200, 200, 200))
draw3.text((120, 180), 'Upload your images for professional enhancement', fill=(33, 37, 41))
draw3.text((120, 220), 'Supports PNG, JPEG, and other common formats', fill=(108, 117, 125))

# Light blur
img3_small = img3.resize((400, 300), Image.LANCZOS)
img3_blurry = img3_small.resize((1200, 900), Image.LANCZOS)
img3_blurry.save('web_interface.png')

# Create a non-PNG file that should be ignored
with open('readme.txt', 'w') as f:
    f.write('This is not a PNG file and should be ignored during enhancement.')

print('Generated 3 blurry PNG screenshots for enhancement testing')