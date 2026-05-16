import random
import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

random.seed(42)

workspace = Path("/workspace")

# Create realistic distractor directory structure
dirs = [
    "assets/images",
    "assets/fonts",
    "assets/icons",
    "docs/legal",
    "docs/internal",
    "marketing/campaigns/q1",
    "marketing/campaigns/q2",
    "marketing/social",
    "presentations/archive",
    "presentations/drafts",
    "data/reports",
    "data/analytics",
    "templates/old",
    "brand/raw",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "assets/images/hero_banner.txt": "hero banner placeholder 1920x1080",
    "assets/fonts/README.txt": "Font files would go here",
    "assets/icons/icon_list.txt": "home, search, settings, user, bell",
    "docs/legal/terms_of_service.txt": "Terms and conditions apply. All rights reserved.",
    "docs/internal/team_roster.csv": "name,role,email\nAlice,PM,alice@example.com\nBob,Engineer,bob@example.com",
    "docs/internal/meeting_notes.txt": "Q3 planning meeting notes. Action items: finalize deck, review metrics.",
    "marketing/campaigns/q1/campaign_brief.txt": "Q1 campaign: focus on enterprise, target CTR 3.5%",
    "marketing/campaigns/q2/campaign_brief.txt": "Q2 campaign: summer push, social amplification",
    "marketing/social/content_calendar.csv": "date,platform,copy\n2024-01-15,LinkedIn,Exciting news!\n2024-01-16,Twitter,Join us",
    "data/reports/monthly_metrics.json": '{"users": 12500, "revenue": 450000, "churn": 0.02}',
    "data/analytics/funnel_data.csv": "stage,users\nAwareness,10000\nConsideration,3200\nDecision,800\nPurchase,200",
    "templates/old/slide_template_v1.txt": "Old template - deprecated. Do not use.",
    "brand/raw/color_ideas.txt": "Maybe use blue? Or green? TBD.",
    "presentations/archive/pitch_v1_notes.txt": "First version notes - very rough draft.",
}

for rel_path, content in distractor_files.items():
    (workspace / rel_path).write_text(content)

# Now create the main artifact: a messy, un-branded PowerPoint presentation
# It will have wrong colors, wrong fonts, mixed sizes, and non-text shapes
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

slide_layout = prs.slide_layouts[6]  # Blank layout

# ---- SLIDE 1: Title slide ----
slide1 = prs.slides.add_slide(slide_layout)

# Big title - 36pt (should become heading -> Poppins, dark bg -> light text)
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def add_textbox(slide, text, left, top, width, height, font_size, bold=False,
                font_name="Times New Roman", fg_color=(0,0,0), bg_color=None):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.name = font_name
    run.font.color.rgb = RGBColor(*fg_color)
    if bg_color:
        from pptx.oxml.ns import qn
        from lxml import etree
        # Set solid fill on the shape
        sp = txBox._element
        spPr = sp.find(qn('p:spPr'))
        if spPr is None:
            spPr = etree.SubElement(sp, qn('p:spPr'))
        solidFill = etree.SubElement(spPr, qn('a:solidFill'))
        srgbClr = etree.SubElement(solidFill, qn('a:srgbClr'))
        srgbClr.set('val', '%02x%02x%02x' % bg_color)
    return txBox

# Slide 1: dark background rectangle + title text
# Add a large rectangle as dark background (non-text shape #1)
bg_rect = slide1.shapes.add_shape(
    1,  # MSO_SHAPE_TYPE.RECTANGLE
    Inches(0), Inches(0), Inches(13.333), Inches(7.5)
)
bg_rect.fill.solid()
bg_rect.fill.fore_color.rgb = RGBColor(0x22, 0x22, 0x22)  # Wrong dark color (should be #141413)
bg_rect.line.fill.background()

# Title textbox - 36pt, wrong font, wrong color
title_box = add_textbox(slide1, "Innovating the Future of AI Collaboration",
                        0.5, 1.5, 12, 2, 36, bold=True,
                        font_name="Times New Roman", fg_color=(255, 0, 0))

# Subtitle textbox - 18pt body text, wrong font
sub_box = add_textbox(slide1, "A strategic overview of our partnership opportunities and the path forward in 2024.",
                      0.5, 4.0, 10, 1.5, 18, bold=False,
                      font_name="Comic Sans MS", fg_color=(200, 200, 200))

# Small accent text - 12pt
accent_box = add_textbox(slide1, "Confidential — Board Presentation",
                         0.5, 6.5, 6, 0.7, 12, bold=False,
                         font_name="Courier New", fg_color=(150, 150, 150))

# ---- SLIDE 2: Content slide ----
slide2 = prs.slides.add_slide(slide_layout)

# Light background rectangle (non-text shape #2)
bg_rect2 = slide2.shapes.add_shape(
    1,
    Inches(0), Inches(0), Inches(13.333), Inches(7.5)
)
bg_rect2.fill.solid()
bg_rect2.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)  # Wrong: pure white instead of #faf9f5
bg_rect2.line.fill.background()

# Section header - 28pt (heading)
h2 = add_textbox(slide2, "Market Opportunity",
                 0.5, 0.3, 12, 1.2, 28, bold=True,
                 font_name="Impact", fg_color=(0, 0, 255))

# Body text - 14pt
body2 = add_textbox(slide2, "The global AI market is projected to reach $1.8 trillion by 2030. "
                             "Our platform captures enterprise workflow automation, reducing overhead by 40%.",
                    0.5, 1.8, 11, 2, 14, bold=False,
                    font_name="Verdana", fg_color=(50, 50, 50))

# Decorative rectangle (non-text shape #3)
deco_rect = slide2.shapes.add_shape(
    1,
    Inches(0.5), Inches(4.0), Inches(3.5), Inches(0.15)
)
deco_rect.fill.solid()
deco_rect.fill.fore_color.rgb = RGBColor(0xFF, 0x00, 0x00)  # Wrong accent
deco_rect.line.fill.background()

# Another decorative rectangle (non-text shape #4)
deco_rect2 = slide2.shapes.add_shape(
    1,
    Inches(4.5), Inches(4.0), Inches(3.5), Inches(0.15)
)
deco_rect2.fill.solid()
deco_rect2.fill.fore_color.rgb = RGBColor(0x00, 0xFF, 0x00)  # Wrong accent
deco_rect2.line.fill.background()

# Small label - 10pt body
label2 = add_textbox(slide2, "Source: Market Intelligence Report 2023",
                     0.5, 6.8, 8, 0.5, 10, bold=False,
                     font_name="Arial", fg_color=(100, 100, 100))

# ---- SLIDE 3: Metrics slide ----
slide3 = prs.slides.add_slide(slide_layout)

bg_rect3 = slide3.shapes.add_shape(
    1,
    Inches(0), Inches(0), Inches(13.333), Inches(7.5)
)
bg_rect3.fill.solid()
bg_rect3.fill.fore_color.rgb = RGBColor(0xEE, 0xEE, 0xEE)  # Wrong light color
bg_rect3.line.fill.background()

# Heading - exactly 24pt (boundary case — MUST be treated as heading)
h3 = add_textbox(slide3, "Key Performance Metrics",
                 0.5, 0.3, 12, 1.1, 24, bold=True,
                 font_name="Times New Roman", fg_color=(0, 0, 0))

# Body text blocks
body3a = add_textbox(slide3, "Monthly Active Users: 125,000\n+18% quarter-over-quarter growth",
                     0.5, 1.8, 5.5, 1.5, 16, bold=False,
                     font_name="Tahoma", fg_color=(80, 80, 80))

body3b = add_textbox(slide3, "Revenue Run Rate: $2.4M ARR\nNet Revenue Retention: 118%",
                     7.0, 1.8, 5.5, 1.5, 16, bold=False,
                     font_name="Tahoma", fg_color=(80, 80, 80))

# Decorative accent shapes (non-text shapes #5 and #6)
accent_shape1 = slide3.shapes.add_shape(
    1,
    Inches(0.5), Inches(3.8), Inches(5.5), Inches(2.5)
)
accent_shape1.fill.solid()
accent_shape1.fill.fore_color.rgb = RGBColor(0xAA, 0x00, 0x00)
accent_shape1.line.fill.background()

accent_shape2 = slide3.shapes.add_shape(
    1,
    Inches(7.0), Inches(3.8), Inches(5.5), Inches(2.5)
)
accent_shape2.fill.solid()
accent_shape2.fill.fore_color.rgb = RGBColor(0x00, 0x00, 0xAA)
accent_shape2.line.fill.background()

# Small text inside accent shapes - 13pt
small1 = add_textbox(slide3, "Growth trajectory exceeds industry benchmark by 2.3x",
                     0.7, 4.0, 5.0, 1.5, 13, bold=False,
                     font_name="Courier New", fg_color=(255, 255, 255))

small2 = add_textbox(slide3, "Churn rate: 1.8% — best-in-class for SMB segment",
                     7.2, 4.0, 5.0, 1.5, 13, bold=False,
                     font_name="Courier New", fg_color=(255, 255, 255))

# Save to presentations/drafts
out_path = workspace / "presentations" / "drafts" / "board_pitch_draft.pptx"
prs.save(str(out_path))

print(f"Generated: {out_path}")
print("Workspace setup complete.")