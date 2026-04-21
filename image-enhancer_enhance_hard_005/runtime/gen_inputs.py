import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Create screenshot image (low quality, needs upscaling)
screenshot_img = Image.new('RGB', (1920, 1080), color=(240, 240, 240))
draw = ImageDraw.Draw(screenshot_img)
# Add some UI elements
draw.rectangle([50, 50, 500, 200], fill=(100, 150, 200), outline=(0, 0, 0))
draw.rectangle([50, 220, 500, 350], fill=(150, 200, 100), outline=(0, 0, 0))
draw.text((60, 60), 'Screenshot Content - Button 1', fill=(255, 255, 255))
draw.text((60, 230), 'Screenshot Content - Button 2', fill=(255, 255, 255))
screenshot_img.save('app_screenshot.jpg', quality=85)

# Create photo image (noisy, needs noise reduction)
photo_img = Image.new('RGB', (800, 600), color=(120, 180, 140))
draw = ImageDraw.Draw(photo_img)
# Add some photo-like content
draw.ellipse([200, 150, 600, 450], fill=(80, 120, 200), outline=(0, 0, 0))
draw.text((250, 280), 'Nature Photo Content', fill=(255, 255, 255))
# Add noise
np_img = np.array(photo_img)
noise = np.random.normal(0, 15, np_img.shape).astype(np.uint8)
noisy_img = np.clip(np_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
photo_noisy = Image.fromarray(noisy_img)
photo_noisy.save('vacation_photo.png')

# Create logo image (needs transparency)
logo_img = Image.new('RGB', (400, 300), color=(255, 255, 255))
draw = ImageDraw.Draw(logo_img)
# Create simple logo shape
draw.ellipse([100, 75, 300, 225], fill=(200, 50, 50), outline=(0, 0, 0))
draw.text((150, 135), 'LOGO', fill=(255, 255, 255))
logo_img.save('company_logo.jpg')

# Create additional test image
test_img = Image.new('RGB', (640, 480), color=(180, 180, 180))
draw = ImageDraw.Draw(test_img)
draw.rectangle([100, 100, 540, 380], fill=(220, 220, 50), outline=(0, 0, 0))
draw.text((120, 120), 'Test Image Content', fill=(0, 0, 0))
test_img.save('test_image.bmp')

print('Generated test images: app_screenshot.jpg, vacation_photo.png, company_logo.jpg, test_image.bmp')