import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Create test images with different characteristics

# Image 1: Low resolution screenshot-like image
img1 = Image.new('RGB', (800, 600), color='white')
draw1 = ImageDraw.Draw(img1)
# Add some text and shapes to simulate a screenshot
draw1.rectangle([50, 50, 750, 550], outline='black', width=2)
draw1.rectangle([100, 100, 300, 200], fill='lightblue', outline='darkblue')
draw1.rectangle([400, 150, 600, 250], fill='lightgreen', outline='darkgreen')
draw1.text((120, 130), 'Dashboard Analytics', fill='black')
draw1.text((420, 180), 'User Metrics', fill='black')
draw1.text((150, 300), 'Performance Report Q4 2024', fill='darkblue')
draw1.text((150, 350), 'Revenue: $2.5M (+15%)', fill='green')
draw1.text((150, 380), 'Users: 45K (+8%)', fill='green')
# Add some compression artifacts by saving as JPEG and reloading
img1.save('temp_compress.jpg', quality=70)
img1 = Image.open('temp_compress.jpg')
img1.save('dashboard-screenshot.png')
os.remove('temp_compress.jpg')

# Image 2: Small blurry image that needs upscaling
img2 = Image.new('RGB', (400, 300), color='lightgray')
draw2 = ImageDraw.Draw(img2)
draw2.ellipse([50, 50, 350, 250], fill='orange', outline='red', width=3)
draw2.text((150, 130), 'LOGO', fill='white')
draw2.text((130, 160), 'Company', fill='white')
# Apply blur to simulate poor quality
import numpy as np
arr = np.array(img2)
# Simple blur simulation
for i in range(1, arr.shape[0]-1):
    for j in range(1, arr.shape[1]-1):
        arr[i, j] = (arr[i-1:i+2, j-1:j+2].mean(axis=(0,1)) * 0.7 + arr[i, j] * 0.3).astype(np.uint8)
img2 = Image.fromarray(arr)
img2.save('company-logo.jpg')

# Image 3: High resolution but needs sharpening
img3 = Image.new('RGB', (1200, 800), color='white')
draw3 = ImageDraw.Draw(img3)
# Create a chart-like visualization
draw3.rectangle([100, 100, 1100, 700], outline='black', width=2)
bars = [(200, 600, 250, 400, 'red'), (300, 600, 350, 350, 'blue'), 
        (400, 600, 450, 300, 'green'), (500, 600, 550, 250, 'orange'),
        (600, 600, 650, 200, 'purple')]
for x1, y1, x2, y2, color in bars:
    draw3.rectangle([x1, y2, x2, y1], fill=color)
draw3.text((200, 650), 'Jan', fill='black')
draw3.text((300, 650), 'Feb', fill='black')
draw3.text((400, 650), 'Mar', fill='black')
draw3.text((500, 650), 'Apr', fill='black')
draw3.text((600, 650), 'May', fill='black')
draw3.text((500, 150), 'Sales Performance Chart', fill='black')
draw3.text((120, 180), 'Monthly Revenue (in thousands)', fill='gray')
img3.save('sales-chart.png')

# Create a file that should be ignored (not an image)
with open('readme.txt', 'w') as f:
    f.write('This is not an image file and should be ignored.')

print('Generated test images:')
print('- dashboard-screenshot.png (800x600, compressed artifacts)')
print('- company-logo.jpg (400x300, blurry, needs upscaling)')
print('- sales-chart.png (1200x800, needs sharpening)')
print('- readme.txt (non-image file to ignore)')