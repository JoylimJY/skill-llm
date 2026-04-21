import os
import json
from PIL import Image, ImageDraw, ImageFont

# Fixed seed for determinism

# Mocked ads data for 3 competitors, 2 platforms each
ads_data = {
    "Figma": {
        "facebook": [
            {
                "id": "fb01",
                "copy": "Design collaboration made easy - Try Figma now",
                "theme": "Collaboration",
                "image_text": "Figma FB Collaboration"
            },
            {
                "id": "fb02",
                "copy": "Stop wasting time on old design tools",
                "theme": "Efficiency"
            }
        ],
        "linkedin": [
            {
                "id": "li01",
                "copy": "Enterprise-ready design system platform",
                "theme": "Enterprise"
            },
            {
                "id": "li02",
                "copy": "Scaling design teams with Figma’s platform",
                "theme": "Scaling"
            }
        ]
    },
    "Airtable": {
        "facebook": [
            {
                "id": "fb01",
                "copy": "Organize anything, with Airtable's flexible tables",
                "theme": "Organization"
            },
            {
                "id": "fb02",
                "copy": "Say goodbye to messy spreadsheets",
                "theme": "Pain Point"
            },
            {
                "id": "fb03",
                "copy": "Power your workflow with Airtable automation",
                "theme": "Automation"
            }
        ],
        "linkedin": [
            {
                "id": "li01",
                "copy": "Trusted by enterprises for data collaboration",
                "theme": "Enterprise"
            },
            {
                "id": "li02",
                "copy": "Connect your teams with Airtable Workspaces",
                "theme": "Collaboration"
            }
        ]
    },
    "Miro": {
        "facebook": [
            {
                "id": "fb01",
                "copy": "Visual collaboration boards to boost creativity",
                "theme": "Creativity"
            },
            {
                "id": "fb02",
                "copy": "Replace meetings with asynchronous boards",
                "theme": "Remote Work"
            }
        ],
        "linkedin": [
            {
                "id": "li01",
                "copy": "Enterprise security meets visual project management",
                "theme": "Enterprise"
            },
            {
                "id": "li02",
                "copy": "Scale agile teams with Miro",
                "theme": "Agile"
            },
            {
                "id": "li03",
                "copy": "Trusted by 10,000+ companies worldwide",
                "theme": "Social Proof"
            }
        ]
    }
}

OUTPUT_ROOT = './competitor-ads'

os.makedirs(OUTPUT_ROOT, exist_ok=True)

# For images, create dummy PNGs with text showing competitor and platform

font = None
try:
    from PIL import ImageFont
    font = ImageFont.load_default()
except:
    font = None

for competitor, platforms in ads_data.items():
    for platform, ads in platforms.items():
        dir_path = os.path.join(OUTPUT_ROOT, competitor.lower(), platform.lower())
        os.makedirs(dir_path, exist_ok=True)
        for ad in ads:
            ad_id = ad.get('id', 'unknown')
            filename = f"{competitor.lower()}_{platform.lower()}_{ad_id}.png"
            path = os.path.join(dir_path, filename)
            # Create a simple image 400x200 with theme and competitor info
            img = Image.new('RGB', (400, 200), color=(240, 240, 240))
            d = ImageDraw.Draw(img)
            lines = [
                f"{competitor} {platform.capitalize()}",
                f"Ad ID: {ad_id}",
                f"Theme: {ad.get('theme','')}",
                'Copy:',
                ad.get('copy','')
            ]
            y = 20
            for line in lines:
                d.text((10, y), line, fill=(0,0,0), font=font)
                y += 20
            img.save(path)

# Also save ads metadata JSON (not required but might help evaluation)
metadata_path = os.path.join(OUTPUT_ROOT, "ads_metadata.json")
with open(metadata_path, 'w') as f:
    json.dump(ads_data, f, indent=2)
