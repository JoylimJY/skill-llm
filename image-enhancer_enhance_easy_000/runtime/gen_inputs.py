import cv2
import numpy as np
from PIL import Image

# Create a test screenshot with some blur and text
width, height = 800, 600
image = np.ones((height, width, 3), dtype=np.uint8) * 240

# Add some colored rectangles to simulate a UI
cv2.rectangle(image, (50, 50), (350, 150), (70, 130, 180), -1)
cv2.rectangle(image, (400, 200), (750, 400), (100, 200, 100), -1)

# Add text to simulate screenshot content
font = cv2.FONT_HERSHEY_SIMPLEX
cv2.putText(image, 'Sample Screenshot', (60, 100), font, 1, (255, 255, 255), 2)
cv2.putText(image, 'Blog Post Image', (410, 300), font, 0.8, (255, 255, 255), 2)
cv2.putText(image, 'Quality: Original', (60, 500), font, 0.6, (50, 50, 50), 1)

# Apply blur to simulate a low-quality screenshot
blurred = cv2.GaussianBlur(image, (5, 5), 0)

# Add some noise
noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
noisy_image = cv2.add(blurred, noise)

# Save as PNG
cv2.imwrite('input_screenshot.png', noisy_image)
print('Generated input_screenshot.png with blur and noise')