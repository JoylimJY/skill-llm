import os
from PIL import Image, ImageDraw, ImageFont

# Create a deterministic set of mock ad data to simulate Facebook ads from Acme Tech
ads = [
    {
        "id": "ad001",
        "image_text": "Tired of slow setups? Switch to Acme Tech!",
        "copy": "Our setup time is 50% faster than competitors.",
        "problem": "slow setup",
        "cta": "Get Started Today"
    },
    {
        "id": "ad002",
        "image_text": "Stop losing data in messy workflows.",
        "copy": "Acme Tech keeps your data secure and organized.",
        "problem": "data loss",
        "cta": "Try for Free"
    },
    {
        "id": "ad003",
        "image_text": "Save money on your IT budget.",
        "copy": "Reduce costs with Acme Tech solutions.",
        "problem": "high costs",
        "cta": "Schedule a Demo"
    },
    {
        "id": "ad004",
        "image_text": "Switch seamlessly with zero downtime.",
        "copy": "No disruptions during migration thanks to Acme Tech.",
        "problem": "downtime",
        "cta": "Learn More"
    },
    {
        "id": "ad005",
        "image_text": "Fast. Secure. Reliable IT.",
        "copy": "Experience fast and reliable IT with Acme Tech.",
        "problem": "general reliability",
        "cta": "Contact Sales"
    }
]

# Create output folder
os.makedirs('acme-facebook-ads', exist_ok=True)

# Create simple PNG images with the image_text as black text on white background
for ad in ads:
    img = Image.new('RGB', (400, 200), color='white')
    d = ImageDraw.Draw(img)

    # Use built-in font (no external dependencies) to avoid font issues
    d.text((10, 80), ad['image_text'], fill='black')

    filename = f"acme-facebook-ads/{ad['id']}.png"
    img.save(filename)

# Generate a JSON file with ad metadata for possible use
import json
with open('acme-facebook-ads/ads_metadata.json', 'w') as f:
    json.dump(ads, f, indent=2)
