import os
import random
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

random.seed(42)

workspace = Path("/workspace")

# Create realistic directory structure with distractors
dirs = [
    "marketing/assets/logos",
    "marketing/assets/images",
    "marketing/campaigns/q4_2024",
    "marketing/campaigns/q3_2024",
    "design/templates/old",
    "design/templates/approved",
    "design/guidelines/drafts",
    "legal/brand_policy",
    "finance/reports",
    "engineering/docs",
    "hr/onboarding",
    "sales/decks/archive",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Create distractor files
distractor_files = {
    "marketing/assets/logos/logo_usage.txt": "Use primary logo on all external materials. Minimum size 40px. Clear space = 1x logo height on all sides.",
    "marketing/campaigns/q4_2024/campaign_brief.txt": "Q4 2024 Campaign: Focus on enterprise customers. Budget: $2.5M. Launch: Nov 1st.",
    "marketing/campaigns/q3_2024/results.csv": "campaign,impressions,clicks,conversions\nBrand Awareness,1200000,45000,3200\nProduct Launch,890000,32000,2800",
    "design/templates/old/DEPRECATED_template_v1.txt": "DEPRECATED: Do not use these color codes. Old brand: #FF0000, #0000FF, #FFFF00",
    "design/templates/approved/template_notes.txt": "Approved templates stored here. Contact design team for access.",
    "design/guidelines/drafts/color_experiments.txt": "Experimental: trying #e8463a for accent. Not approved. Do not use.",
    "legal/brand_policy/usage_policy.txt": "Brand assets may only be used for official Anthropic communications. External usage requires written approval.",
    "finance/reports/q3_summary.txt": "Q3 revenue up 34% YoY. Detailed breakdown available upon request.",
    "engineering/docs/api_reference.txt": "API v2.1 reference. Authentication: Bearer token. Rate limit: 1000 req/min.",
    "hr/onboarding/welcome_guide.txt": "Welcome to Anthropic! Your first week: team introductions, tool access, and orientation sessions.",
    "sales/decks/archive/old_pitch.txt": "ARCHIVED 2023 sales pitch. Numbers outdated, do not use.",
    "marketing/assets/images/image_manifest.txt": "hero_image_v3.png - approved\nproduct_screenshot_v2.png - approved\nblog_banner_draft.png - needs review",
}
for path, content in distractor_files.items():
    (workspace / path).write_text(content)

# Create a fake "wrong" brand colors file to mislead
(workspace / "design/guidelines/drafts/unofficial_colors.json").write_text(
    '{"primary": "#FF6B35", "secondary": "#004E89", "background": "#FFFFFF", "text": "#333333"}'
)

# Now create the MAIN INPUT: a messy, unstyled PowerPoint deck
# This deck has wrong/no brand colors, wrong fonts, and shapes without brand accents

prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)

slide_layouts = prs.slide_layouts

# --- Slide 1: Title Slide ---
slide1 = prs.slides.add_slide(slide_layouts[6])  # blank layout

# Background rectangle (full slide) - currently wrong color
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor

def add_rect(slide, left, top, width, height, fill_rgb, text=None, font_size=None, font_bold=False, text_rgb=None, font_name=None):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Emu(left), Emu(top), Emu(width), Emu(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(*fill_rgb)
    shape.line.fill.background()
    if text is not None:
        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = text
        run.font.size = Pt(font_size) if font_size else Pt(18)
        run.font.bold = font_bold
        if text_rgb:
            run.font.color.rgb = RGBColor(*text_rgb)
        if font_name:
            run.font.name = font_name
    return shape

slide_w = int(prs.slide_width)
slide_h = int(prs.slide_height)

# Slide 1: Title slide - background should be dark (#141413), text light (#faf9f5)
# Currently has wrong colors
bg1 = add_rect(slide1, 0, 0, slide_w, slide_h, (30, 30, 100))  # wrong blue bg
title1 = add_rect(
    slide1,
    Inches(1), Inches(2.5), Inches(11.33), Inches(1.5),
    (30, 30, 100),  # wrong color
    text="Anthropic Quarterly Business Review",
    font_size=36,  # heading - should get Poppins
    font_bold=True,
    text_rgb=(200, 200, 200),  # wrong text color
    font_name="Times New Roman"  # wrong font
)

sub1 = add_rect(
    slide1,
    Inches(1), Inches(4.2), Inches(11.33), Inches(0.8),
    (30, 30, 100),
    text="Q4 2024 | Prepared by the Marketing Team",
    font_size=18,  # body - should get Lora
    text_rgb=(180, 180, 180),  # wrong
    font_name="Times New Roman"
)

# --- Slide 2: Agenda slide ---
slide2 = prs.slides.add_slide(slide_layouts[6])

# Light background slide - should use #faf9f5
bg2 = add_rect(slide2, 0, 0, slide_w, slide_h, (255, 255, 255))  # wrong pure white

heading2 = add_rect(
    slide2,
    Inches(0.5), Inches(0.4), Inches(12.33), Inches(1.0),
    (255, 255, 255),
    text="Agenda",
    font_size=28,  # heading >= 24pt - should get Poppins
    font_bold=True,
    text_rgb=(0, 0, 0),  # wrong pure black, should be #141413
    font_name="Helvetica"
)

body2 = add_rect(
    slide2,
    Inches(0.5), Inches(1.6), Inches(8), Inches(4),
    (255, 255, 255),
    text="1. Company Highlights\n2. Product Updates\n3. Market Expansion\n4. Financial Overview\n5. Q1 2025 Roadmap",
    font_size=18,  # body - should get Lora
    text_rgb=(50, 50, 50),  # wrong
    font_name="Helvetica"
)

# Accent shapes - should cycle: orange, blue, green
accent_box1 = add_rect(
    slide2,
    Inches(9.5), Inches(1.5), Inches(0.15), Inches(4),
    (255, 0, 0)  # wrong red, should be orange (#d97757) - 1st accent shape
)

accent_box2 = add_rect(
    slide2,
    Inches(10), Inches(2), Inches(2.8), Inches(0.6),
    (255, 0, 0)  # wrong red, should be blue (#6a9bcc) - 2nd accent shape
)

accent_box3 = add_rect(
    slide2,
    Inches(10), Inches(3), Inches(2.8), Inches(0.6),
    (255, 0, 0)  # wrong red, should be green (#788c5d) - 3rd accent shape
)

# --- Slide 3: Content slide ---
slide3 = prs.slides.add_slide(slide_layouts[6])

# Dark background
bg3 = add_rect(slide3, 0, 0, slide_w, slide_h, (20, 20, 80))  # wrong

heading3 = add_rect(
    slide3,
    Inches(0.5), Inches(0.3), Inches(12.33), Inches(1.0),
    (20, 20, 80),
    text="Product Highlights & Innovation",
    font_size=30,  # heading >=24pt - should get Poppins
    font_bold=True,
    text_rgb=(240, 240, 240),
    font_name="Arial Black"
)

body3 = add_rect(
    slide3,
    Inches(0.5), Inches(1.5), Inches(6), Inches(4),
    (20, 20, 80),
    text="Claude 3.5 Sonnet leads industry benchmarks across reasoning, coding, and analysis tasks. Enterprise adoption increased 3x year-over-year.",
    font_size=16,  # body - should get Lora
    text_rgb=(200, 200, 200),
    font_name="Courier New"  # wrong font
)

# More accent shapes for cycling test
accent3a = add_rect(
    slide3,
    Inches(7), Inches(1.5), Inches(5.5), Inches(1.2),
    (100, 100, 200)  # wrong, should be orange (4th accent = cycles back to orange)
)

accent3b = add_rect(
    slide3,
    Inches(7), Inches(3), Inches(5.5), Inches(1.2),
    (100, 100, 200)  # wrong, should be blue (5th accent)
)

accent3c = add_rect(
    slide3,
    Inches(7), Inches(4.5), Inches(5.5), Inches(1.2),
    (100, 100, 200)  # wrong, should be green (6th accent)
)

# --- Slide 4: Financial Summary ---
slide4 = prs.slides.add_slide(slide_layouts[6])

bg4 = add_rect(slide4, 0, 0, slide_w, slide_h, (245, 245, 245))  # close to but not the right light bg

heading4 = add_rect(
    slide4,
    Inches(0.5), Inches(0.3), Inches(12.33), Inches(1.0),
    (245, 245, 245),
    text="Financial Overview",
    font_size=26,  # heading >= 24pt
    font_bold=True,
    text_rgb=(10, 10, 10),
    font_name="Impact"  # wrong font
)

small_heading4 = add_rect(
    slide4,
    Inches(0.5), Inches(1.5), Inches(5), Inches(0.6),
    (245, 245, 245),
    text="Revenue Growth",
    font_size=20,  # body text < 24pt - should get Lora
    font_bold=True,
    text_rgb=(10, 10, 10),
    font_name="Impact"
)

body4 = add_rect(
    slide4,
    Inches(0.5), Inches(2.2), Inches(5.5), Inches(3),
    (245, 245, 245),
    text="Annual recurring revenue exceeded targets by 28%. Customer retention rate: 94%. New enterprise contracts: 127 signed in Q4.",
    font_size=14,  # body - should get Lora
    text_rgb=(30, 30, 30),
    font_name="Verdana"
)

# Accent shapes on this slide
accent4a = add_rect(
    slide4,
    Inches(6.5), Inches(1.5), Inches(6), Inches(2),
    (200, 50, 50)  # wrong, should be orange (7th accent = cycles: orange)
)

accent4b = add_rect(
    slide4,
    Inches(6.5), Inches(4), Inches(6), Inches(1.5),
    (200, 50, 50)  # wrong, should be blue (8th accent)
)

# Save the presentation
output_path = workspace / "marketing" / "campaigns" / "q4_2024" / "quarterly_review_DRAFT.pptx"
prs.save(str(output_path))

print(f"Created draft presentation: {output_path}")
print("Workspace structure created successfully.")