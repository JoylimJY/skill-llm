import os
import json

# Create a mock local 'Facebook Ad Library' JSON response
ads_data = {
    "ads": [
        {
            "id": "ad001",
            "image_url": "ad001.png",
            "copy": "Tired of juggling multiple tools? Try Acme Productivity for seamless workflow!",
            "cta": "Try now",
            "theme": "tool sprawl",
            "active": True
        },
        {
            "id": "ad002",
            "image_url": "ad002.png",
            "copy": "Cut meeting times by 50% with async updates.",
            "cta": "Get started",
            "theme": "meeting overload",
            "active": True
        },
        {
            "id": "ad003",
            "image_url": "ad003.png",
            "copy": "Keep your team aligned with real-time collaboration.",
            "cta": "Learn more",
            "theme": "collaboration",
            "active": True
        },
        {
            "id": "ad004",
            "image_url": "ad004.png",
            "copy": "Legacy ad, not active",
            "cta": "",
            "theme": "old",
            "active": False
        }
    ]
}

os.makedirs("acme-ads", exist_ok=True)

# Generate dummy PNG screenshots (small, single-color images with text)
from PIL import Image, ImageDraw, ImageFont

for ad in ads_data["ads"]:
    filename = os.path.join("acme-ads", ad["image_url"])
    img = Image.new('RGB', (400, 200), color = (73, 109, 137))
    d = ImageDraw.Draw(img)
    # Draw ad id as text
    d.text((10, 80), ad["id"], fill=(255,255,0))
    img.save(filename)

# Save the ads json data for reference
with open("acme-ads/ads_data.json", "w") as f:
    json.dump(ads_data, f, indent=2)
