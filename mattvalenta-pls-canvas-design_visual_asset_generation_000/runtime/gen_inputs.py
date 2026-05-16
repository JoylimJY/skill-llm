import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---

dirs = [
    "brand/archive/2022",
    "brand/archive/2023",
    "brand/current/logos",
    "brand/current/typography",
    "events/hackathon_2024/raw_assets",
    "events/hackathon_2024/final",
    "events/hackathon_2024/drafts",
    "events/past/2023_summit",
    "internal/templates/pdf",
    "internal/templates/png",
    "internal/guidelines",
    "tools/scripts",
    "tools/configs",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "brand/archive/2022/color_palette_v1.json": json.dumps({
        "primary": "#FF0000", "secondary": "#0000FF", "accent": "#FFFF00"
    }),
    "brand/archive/2023/color_palette_v2.json": json.dumps({
        "primary": "#1A1A2E", "secondary": "#16213E", "accent": "#E94560"
    }),
    "brand/current/logos/logo_spec.txt": "Logo: 200x200px, SVG preferred. Min size 32px.",
    "brand/current/typography/font_guide.txt": "Primary: Inter. Fallback: Arial. Sizes: H1=48, H2=32, Body=16.",
    "events/hackathon_2024/raw_assets/schedule_data.json": json.dumps({
        "event": "NovaSpark Hackathon 2024",
        "date": "October 12, 2024",
        "venue": "Building C, Innovation Hub",
        "sessions": [
            {"time": "09:00", "title": "Opening Keynote"},
            {"time": "10:30", "title": "Team Formation & Briefing"},
            {"time": "12:00", "title": "Lunch Break"},
            {"time": "14:00", "title": "Hacking Begins"},
            {"time": "20:00", "title": "Demo Presentations"},
            {"time": "21:30", "title": "Awards Ceremony"},
        ]
    }),
    "events/hackathon_2024/raw_assets/copywriting.txt": (
        "Tagline: 'Build. Break. Innovate.'\n"
        "Body: Join us for 12 hours of intense building, collaboration, and creativity.\n"
        "Call to action: Register at novaspark.internal/hackathon2024\n"
    ),
    "events/hackathon_2024/drafts/layout_notes.txt": (
        "Poster layout idea:\n"
        "- Top: Event name large\n"
        "- Middle: Date and venue\n"
        "- Bottom: CTA\n"
        "Design note: Event poster should feel modern and translucent (frosted glass look).\n"
        "Schedule doc: Should feel bold and stark, like industrial print.\n"
    ),
    "events/past/2023_summit/poster_old.txt": "Old poster text placeholder. Do not reuse.",
    "internal/templates/pdf/base_template_notes.txt": "PDF base: A4, margins 15mm all sides.",
    "internal/templates/png/canvas_sizes.txt": "Standard poster: 800x600px. Social: 1080x1080px.",
    "internal/guidelines/brand_do_dont.txt": (
        "DO: Use approved fonts.\nDO: Maintain contrast ratios.\n"
        "DON'T: Use gradients from 2022 palette.\nDON'T: Stretch logos.\n"
    ),
    "tools/scripts/resize_helper.py": "# Placeholder resize utility\nprint('resize helper')\n",
    "tools/configs/export_config.json": json.dumps({
        "default_dpi": 150,
        "png_compression": 6,
        "pdf_version": "1.4"
    }),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace initialized successfully.")
print(f"Created {len(distractor_files)} distractor files across {len(dirs)} directories.")