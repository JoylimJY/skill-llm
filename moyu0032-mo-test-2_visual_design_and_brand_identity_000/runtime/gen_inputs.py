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

# Create a realistic distractor directory structure
dirs = [
    "assets/images",
    "assets/icons",
    "assets/fonts",
    "brand_old/2022",
    "brand_old/2023",
    "decks/drafts",
    "decks/final",
    "decks/archived",
    "templates/generic",
    "templates/investor",
    "docs/guidelines",
    "scripts/utils",
    "reports/q3",
    "reports/q4",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Create distractor files
distractor_files = {
    "assets/fonts/font_list.txt": "Arial\nHelvetica\nTimes New Roman\nGeorgia\nVerdana\n",
    "brand_old/2022/colors.txt": "Primary: #003366\nSecondary: #FF6600\nAccent: #009933\n",
    "brand_old/2023/colors.txt": "Primary: #1a1a2e\nSecondary: #e94560\nAccent: #0f3460\n",
    "brand_old/2022/brand_guide.md": "# Old Brand Guide 2022\n\nDo not use these colors anymore.\n\nHeadings: Helvetica 28pt\nBody: Times New Roman 12pt\n",
    "brand_old/2023/typography.md": "# Typography 2023\n\nHeadings font: Roboto\nBody font: Open Sans\n",
    "docs/guidelines/accessibility.md": "# Accessibility Guidelines\n\nUse high contrast ratios.\nMinimum font size: 10pt\n",
    "docs/guidelines/presentation_tips.md": "# Presentation Tips\n\nKeep slides concise.\nUse bullet points.\nMax 6 bullets per slide.\n",
    "templates/generic/slide_master_notes.txt": "Generic template - not branded.\nBackground: white\nText: black\n",
    "templates/investor/checklist.txt": "[] Cover slide\n[] Problem statement\n[] Solution\n[] Market size\n[] Team\n[] Financials\n",
    "scripts/utils/color_converter.py": "def hex_to_rgb(hex_color):\n    hex_color = hex_color.lstrip('#')\n    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))\n",
    "reports/q3/summary.txt": "Q3 Results: Revenue up 23%\nUser growth: +45%\n",
    "reports/q4/summary.txt": "Q4 Projections: Revenue target $2.4M\n",
    "assets/images/placeholder.txt": "Image assets go here (PNG, SVG formats)\n",
    "assets/icons/placeholder.txt": "Icon assets go here\n",
}

for filepath, content in distractor_files.items():
    (workspace / filepath).write_text(content)

# Create a messy, unbranded raw draft PowerPoint presentation
prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)

slide_layout = prs.slide_layouts[6]  # blank layout

# ── Slide 1: Title slide ──────────────────────────────────────────────────────
slide1 = prs.slides.add_slide(slide_layout)

# Wrong background color (should become dark brand background)
bg = slide1.background
fill = bg.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0x33, 0x33, 0x33)  # wrong dark color

# Title text box - large heading (should be 36pt, Poppins)
txBox = slide1.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11), Inches(1.5))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Investor Pitch Deck 2024"
run = p.runs[0]
run.font.size = Pt(36)
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)  # wrong white, should be brand Light
run.font.name = "Helvetica"  # wrong font, should be Poppins

# Subtitle text box - body text (18pt, should be Lora)
txBox2 = slide1.shapes.add_textbox(Inches(1), Inches(4.2), Inches(11), Inches(0.8))
tf2 = txBox2.text_frame
p2 = tf2.paragraphs[0]
p2.text = "Transforming the Future of AI-Assisted Work"
run2 = p2.runs[0]
run2.font.size = Pt(18)
run2.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)  # wrong gray
run2.font.name = "Helvetica"  # wrong font, should be Lora

# A non-text shape (rectangle, accent shape) - wrong color
rect1 = slide1.shapes.add_shape(
    1,  # MSO_SHAPE_TYPE.RECTANGLE
    Inches(1), Inches(6.5), Inches(3), Inches(0.3)
)
rect1.fill.solid()
rect1.fill.fore_color.rgb = RGBColor(0xFF, 0x00, 0x00)  # wrong red, should be orange accent

# ── Slide 2: Problem Statement ────────────────────────────────────────────────
slide2 = prs.slides.add_slide(slide_layout)

bg2 = slide2.background
fill2 = bg2.fill
fill2.solid()
fill2.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)  # wrong white, should be brand Light

# Section heading (28pt, should be Poppins)
txBox3 = slide2.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(12), Inches(1.2))
tf3 = txBox3.text_frame
p3 = tf3.paragraphs[0]
p3.text = "The Problem We Solve"
run3 = p3.runs[0]
run3.font.size = Pt(28)
run3.font.color.rgb = RGBColor(0x00, 0x00, 0x00)  # wrong black, should be brand Dark
run3.font.name = "Arial"  # close but wrong: should be Poppins

# Body text box 1 (14pt, should be Lora)
txBox4 = slide2.shapes.add_textbox(Inches(0.5), Inches(1.8), Inches(6), Inches(3))
tf4 = txBox4.text_frame
tf4.word_wrap = True
for bullet_text in [
    "Knowledge workers spend 40% of time on repetitive tasks",
    "Existing tools lack contextual intelligence",
    "Enterprise AI adoption remains below 15%",
]:
    p4 = tf4.add_paragraph()
    p4.text = bullet_text
    run4 = p4.runs[0]
    run4.font.size = Pt(14)
    run4.font.color.rgb = RGBColor(0x33, 0x33, 0x33)  # wrong
    run4.font.name = "Times New Roman"  # wrong, should be Lora

# Non-text accent shape 1 - wrong color (should be blue - 2nd accent)
rect2 = slide2.shapes.add_shape(
    1,
    Inches(7), Inches(1.8), Inches(5.5), Inches(3)
)
rect2.fill.solid()
rect2.fill.fore_color.rgb = RGBColor(0x00, 0x80, 0x00)  # wrong green

# Non-text accent shape 2 - wrong color (should be green - 3rd accent)
rect3 = slide2.shapes.add_shape(
    1,
    Inches(7), Inches(5.2), Inches(5.5), Inches(0.8)
)
rect3.fill.solid()
rect3.fill.fore_color.rgb = RGBColor(0x80, 0x00, 0x80)  # wrong purple

# ── Slide 3: Solution ─────────────────────────────────────────────────────────
slide3 = prs.slides.add_slide(slide_layout)

bg3 = slide3.background
fill3 = bg3.fill
fill3.solid()
fill3.fore_color.rgb = RGBColor(0x1a, 0x1a, 0x1a)  # nearly dark but wrong

# Main heading (32pt, should be Poppins)
txBox5 = slide3.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1.2))
tf5 = txBox5.text_frame
p5 = tf5.paragraphs[0]
p5.text = "Our Solution: Contextual AI Platform"
run5 = p5.runs[0]
run5.font.size = Pt(32)
run5.font.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)  # nearly light but wrong
run5.font.name = "Georgia"  # wrong, should be Poppins

# Subheading (20pt - BELOW 24pt threshold, should be Lora)
txBox6 = slide3.shapes.add_textbox(Inches(0.5), Inches(1.6), Inches(12), Inches(0.8))
tf6 = txBox6.text_frame
p6 = tf6.paragraphs[0]
p6.text = "Enterprise-grade intelligence, finally accessible"
run6 = p6.runs[0]
run6.font.size = Pt(20)
run6.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)  # wrong
run6.font.name = "Calibri"  # wrong, should be Lora (body, <24pt)

# Body text (12pt, should be Lora)
txBox7 = slide3.shapes.add_textbox(Inches(0.5), Inches(2.6), Inches(7), Inches(3.5))
tf7 = txBox7.text_frame
tf7.word_wrap = True
body_lines = [
    "Seamless integration with existing workflows",
    "Real-time contextual suggestions powered by LLMs",
    "SOC 2 Type II certified infrastructure",
    "99.9% SLA with enterprise support",
]
for line in body_lines:
    pb = tf7.add_paragraph()
    pb.text = line
    rb = pb.runs[0]
    rb.font.size = Pt(12)
    rb.font.color.rgb = RGBColor(0xAA, 0xAA, 0xAA)  # wrong
    rb.font.name = "Calibri"  # wrong

# Two accent shapes on slide 3
shape_a = slide3.shapes.add_shape(1, Inches(8), Inches(2), Inches(4.5), Inches(2))
shape_a.fill.solid()
shape_a.fill.fore_color.rgb = RGBColor(0xFF, 0xA5, 0x00)  # close to orange but wrong

shape_b = slide3.shapes.add_shape(1, Inches(8), Inches(4.5), Inches(4.5), Inches(1.5))
shape_b.fill.solid()
shape_b.fill.fore_color.rgb = RGBColor(0x00, 0x00, 0xFF)  # wrong blue

# ── Slide 4: Team slide ───────────────────────────────────────────────────────
slide4 = prs.slides.add_slide(slide_layout)

bg4 = slide4.background
fill4 = bg4.fill
fill4.solid()
fill4.fore_color.rgb = RGBColor(0xF5, 0xF5, 0xF5)  # close to light but wrong

# Heading (26pt, should be Poppins)
txBox8 = slide4.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(12), Inches(1.0))
tf8 = txBox8.text_frame
p8 = tf8.paragraphs[0]
p8.text = "Meet the Team"
run8 = p8.runs[0]
run8.font.size = Pt(26)
run8.font.color.rgb = RGBColor(0x22, 0x22, 0x22)  # wrong
run8.font.name = "Verdana"  # wrong

# Name labels (16pt body, Lora)
names = ["Dr. Sarah Chen, CEO", "Marcus Rivera, CTO", "Aiko Tanaka, Head of Research"]
for i, name in enumerate(names):
    tb = slide4.shapes.add_textbox(Inches(0.5 + i * 4.1), Inches(5.2), Inches(3.8), Inches(0.6))
    tf_n = tb.text_frame
    pn = tf_n.paragraphs[0]
    pn.text = name
    rn = pn.runs[0]
    rn.font.size = Pt(16)
    rn.font.color.rgb = RGBColor(0x55, 0x55, 0x55)  # wrong
    rn.font.name = "Helvetica"  # wrong

# Accent shape for slide 4
accent4 = slide4.shapes.add_shape(1, Inches(0.5), Inches(1.5), Inches(12), Inches(0.05))
accent4.fill.solid()
accent4.fill.fore_color.rgb = RGBColor(0xCC, 0x44, 0x44)  # wrong

# Save the messy presentation
output_path = workspace / "decks" / "drafts" / "investor_pitch_raw.pptx"
prs.save(str(output_path))
print(f"Created messy draft: {output_path}")

# Create a secondary smaller deck that also needs branding
prs2 = Presentation()
prs2.slide_width = Inches(13.33)
prs2.slide_height = Inches(7.5)

slide_l = prs2.slides.add_slide(prs2.slide_layouts[6])
bg_l = slide_l.background
fill_l = bg_l.fill
fill_l.solid()
fill_l.fore_color.rgb = RGBColor(0x00, 0x40, 0x80)  # wrong navy

txBox_l = slide_l.shapes.add_textbox(Inches(1), Inches(3), Inches(11), Inches(1.5))
tf_l = txBox_l.text_frame
p_l = tf_l.paragraphs[0]
p_l.text = "Product Overview"
r_l = p_l.runs[0]
r_l.font.size = Pt(30)
r_l.font.name = "Comic Sans MS"  # very wrong
r_l.font.color.rgb = RGBColor(0xFF, 0xFF, 0x00)  # wrong yellow

shape_l = slide_l.shapes.add_shape(1, Inches(1), Inches(5), Inches(5), Inches(1))
shape_l.fill.solid()
shape_l.fill.fore_color.rgb = RGBColor(0x80, 0x00, 0x80)

prs2.save(str(workspace / "decks" / "drafts" / "product_overview_raw.pptx"))
print("Created secondary draft.")

# Create a wrong-color reference file as a distractor
(workspace / "brand_old" / "2023" / "wrong_colors.json").write_text(
    '{"primary": "#003366", "secondary": "#FF6600", "accent": "#009933"}\n'
)

print("Workspace setup complete.")