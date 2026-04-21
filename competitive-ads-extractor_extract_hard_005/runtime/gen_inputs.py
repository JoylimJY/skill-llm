import os
from PIL import Image, ImageDraw, ImageFont
import random

random.seed(42)

companies = [
    {
        "name": "Acme CRM",
        "folder": "acme-crm",
        "ads": [
            {"copy": "Boost your sales pipeline with Acme CRM", "cta": "Get started free", "theme": "Sales Efficiency", "format": "static image"},
            {"copy": "Track leads seamlessly in one place", "cta": "Try demo", "theme": "Lead Management", "format": "video"},
            {"copy": "Simplify client management today", "cta": "Start trial", "theme": "Client Management", "format": "static image"},
            {"copy": "Close deals faster with automation", "cta": "Learn more", "theme": "Automation", "format": "video"},
            {"copy": "Your all-in-one sales tool", "cta": "Sign up now", "theme": "All-in-one", "format": "static image"}
        ]
    },
    {
        "name": "BrightTech Solutions",
        "folder": "brighttech-solutions",
        "ads": [
            {"copy": "Power your IT with BrightTech's cloud solutions", "cta": "Contact us", "theme": "Cloud Computing", "format": "video"},
            {"copy": "Secure and scalable infrastructure", "cta": "Get a quote", "theme": "Security", "format": "static image"},
            {"copy": "Experience 99.9% uptime guaranteed", "cta": "Learn more", "theme": "Reliability", "format": "static image"},
            {"copy": "Flexible pricing for businesses of all sizes", "cta": "See plans", "theme": "Pricing", "format": "video"},
            {"copy": "24/7 expert support whenever you need it", "cta": "Contact support", "theme": "Support", "format": "static image"},
            {"copy": "Migrate easily with minimal downtime", "cta": "Get started", "theme": "Migration", "format": "video"}
        ]
    },
    {
        "name": "DataWise Analytics",
        "folder": "datawise-analytics",
        "ads": [
            {"copy": "Unlock insights with DataWise Analytics", "cta": "Request demo", "theme": "Data Insights", "format": "static image"},
            {"copy": "Predict trends before your competitors", "cta": "Join now", "theme": "Predictive Analytics", "format": "video"},
            {"copy": "Make data-driven decisions confidently", "cta": "Try free trial", "theme": "Decision Support", "format": "static image"},
            {"copy": "Integrate with your existing tools seamlessly", "cta": "See integrations", "theme": "Integration", "format": "video"}
        ]
    }
]

# Function to create a simple PNG ad image with text overlay

def create_ad_image(text, path):
    img = Image.new('RGB', (400, 200), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    # Use a common font or default
    try:
        font = ImageFont.truetype('DejaVuSans-Bold.ttf', 16)
    except IOError:
        font = ImageFont.load_default()
    # Split text across 2 lines if too long
    lines = []
    if len(text) > 40:
        mid = len(text)//2
        # split at space closest to middle
        space_before = text.rfind(' ',0,mid)
        space_after = text.find(' ',mid)
        split_at = space_before if space_before != -1 else space_after if space_after != -1 else mid
        lines = [text[:split_at].strip(), text[split_at:].strip()]
    else:
        lines = [text]
    y_text = 80
    for line in lines:
        w, h = d.textsize(line, font=font)
        d.text(((400 - w) / 2, y_text), line, font=font, fill=(255, 255, 255))
        y_text += h + 5
    img.save(path)


for company in companies:
    folder = company['folder']
    os.makedirs(folder, exist_ok=True)
    ads = company['ads']

    for i, ad in enumerate(ads, 1):
        filename = f"ad_{i:03}.png"
        filepath = os.path.join(folder, filename)
        create_ad_image(ad['copy'], filepath)

    # Save raw ads data as JSON for eval reference
    import json
    with open(os.path.join(folder, 'raw_ads.json'), 'w') as f:
        json.dump(ads, f, indent=2)
