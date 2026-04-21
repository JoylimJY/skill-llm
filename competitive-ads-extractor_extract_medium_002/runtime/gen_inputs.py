import os
import json
from PIL import Image, ImageDraw, ImageFont

# Fixed seed for reproducibility
seed = 12345

# Create deterministic fake ads dataset for Acme Software
ads_data = [
    {
        "id": "ad-001",
        "headline": "Struggle with project delays?",
        "body": "Our solution cuts your project delivery time by 30%.",
        "problem": "Project delays",
        "use_case": "Project management",
        "value_prop": "Speed up delivery",
        "creative_pattern": "Before/After visuals"
    },
    {
        "id": "ad-002",
        "headline": "Keep your team aligned effortlessly",
        "body": "Real-time updates and centralized communication.",
        "problem": "Team misalignment",
        "use_case": "Team collaboration",
        "value_prop": "Better communication",
        "creative_pattern": "Product demo video"
    },
    {
        "id": "ad-003",
        "headline": "Stop losing track of tasks",
        "body": "Track every assignment with our intuitive dashboard.",
        "problem": "Task tracking issues",
        "use_case": "Task management",
        "value_prop": "Improved oversight",
        "creative_pattern": "Dashboard screenshot"
    }
]

# Create folder
output_dir = os.path.join("competitor-ads", "acme-software")
os.makedirs(output_dir, exist_ok=True)

# Save each ad's screenshot as PNG with headline text
for ad in ads_data:
    img_path = os.path.join(output_dir, f"{ad['id']}.png")
    img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Use basic font
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    draw.text((20, 180), f"{ad['headline']}", fill="black", font=font)

    img.save(img_path)

# Save raw ads JSON inside folder for reference
with open(os.path.join(output_dir, "ads.json"), "w", encoding="utf-8") as f:
    json.dump(ads_data, f, indent=2)
