import numpy as np
from PIL import Image
import os

# Create a low-quality screenshot with identifiable content
width, height = 800, 600
img_array = np.zeros((height, width, 3), dtype=np.uint8)

# Add some geometric patterns and text-like elements for enhancement verification
# Add a grid pattern
for i in range(0, height, 50):
    img_array[i:i+2, :] = [100, 100, 100]
for j in range(0, width, 50):
    img_array[:, j:j+2] = [100, 100, 100]

# Add some colored rectangles to simulate UI elements
img_array[100:200, 150:350] = [64, 128, 255]  # Blue rectangle
img_array[300:400, 200:500] = [255, 128, 64]  # Orange rectangle
img_array[450:550, 100:300] = [128, 255, 64]  # Green rectangle

# Add some noise to simulate low quality
np.random.seed(42)
noise = np.random.randint(-20, 20, (height, width, 3))
img_array = np.clip(img_array.astype(int) + noise, 0, 255).astype(np.uint8)

# Create PIL image and save
img = Image.fromarray(img_array)
# Compress to simulate low quality
img = img.resize((400, 300))  # Downscale first
img = img.resize((800, 600), Image.NEAREST)  # Upscale with poor quality
img.save('input_screenshot.png', 'PNG')

print('Created input_screenshot.png with low quality')