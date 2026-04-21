import os
from PIL import Image, ImageDraw, ImageFont
import random

# Set deterministic seed
random.seed(42)

# Create multiple low-quality screenshots
screenshots = [
    ('screenshot1.png', (800, 600), 'Application Settings'),
    ('ui-capture.png', (1024, 768), 'Dashboard Overview'),
    ('demo-screen.png', (900, 675), 'User Profile Page')
]

for filename, size, title in screenshots:
    # Create a simple screenshot-like image
    img = Image.new('RGB', size, color=(240, 240, 245))
    draw = ImageDraw.Draw(img)
    
    # Add title bar
    draw.rectangle([0, 0, size[0], 30], fill=(100, 100, 120))
    
    # Add window content
    draw.rectangle([20, 50, size[0]-20, size[1]-20], fill=(255, 255, 255), outline=(200, 200, 200))
    
    # Add some UI elements
    draw.rectangle([40, 80, size[0]-40, 110], fill=(230, 230, 230))
    draw.rectangle([40, 130, 200, 160], fill=(70, 130, 180))
    draw.rectangle([40, 180, 300, 210], fill=(200, 200, 200))
    
    # Add text markers for verification
    try:
        # Try to use default font, fallback to basic if not available
        draw.text((50, 85), f'{title} - Resolution: {size[0]}x{size[1]}', fill=(50, 50, 50))
        draw.text((50, 135), 'Button Element', fill=(255, 255, 255))
        draw.text((50, 185), 'Text Input Field', fill=(80, 80, 80))
        draw.text((10, 8), title, fill=(255, 255, 255))
    except:
        # Fallback if font issues
        pass
    
    # Add some noise to simulate compression artifacts
    pixels = img.load()
    for _ in range(size[0] * size[1] // 100):
        x = random.randint(0, size[0]-1)
        y = random.randint(0, size[1]-1)
        r, g, b = pixels[x, y]
        noise = random.randint(-10, 10)
        pixels[x, y] = (
            max(0, min(255, r + noise)),
            max(0, min(255, g + noise)),
            max(0, min(255, b + noise))
        )
    
    # Save with some compression to simulate low quality
    img.save(filename, 'PNG', optimize=True)

print('Generated 3 low-quality PNG screenshots for enhancement')