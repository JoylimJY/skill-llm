import os
import json

# Create a deterministic sample ad data mimicking Facebook Ad Library scrape for AcmeCorp
ads = [
    {
        "id": "ad-001",
        "title": "Stop wasting time on manual tasks",
        "copy": "AcmeCorp automates your workflow in minutes.",
        "image_desc": "Screenshot of an app dashboard showing automation flows",
        "theme": "Automation",
        "format": "image",
        "cta": "Try free"
    },
    {
        "id": "ad-002",
        "title": "Reduce errors and cut costs",
        "copy": "Our AI-powered system catches mistakes before they happen.",
        "image_desc": "Dashboard with error notifications and cost savings",
        "theme": "Error Reduction",
        "format": "image",
        "cta": "Get started"
    }
]

# Save simulated ads data as JSON for reference
with open('acmecorp_ads.json', 'w') as f:
    json.dump(ads, f, indent=2)

# Generate dummy screenshots as text files named with .png (simulated image files with marker text inside)
os.makedirs('acmecorp-ads', exist_ok=True)

for ad in ads:
    filename = os.path.join('acmecorp-ads', f"{ad['id']}.png")
    with open(filename, 'w') as f:
        f.write(f"Simulated screenshot image for {ad['id']}\nDescription: {ad['image_desc']}\n[MARKER-ACME-SCREENSHOT]")
