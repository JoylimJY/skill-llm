import os
import random
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

random.seed(42)

workspace = "/workspace"

# --- Create distractor directory structure ---
dirs = [
    "marketing/campaigns/q3_launch",
    "marketing/campaigns/q4_planning",
    "marketing/assets/logos",
    "marketing/assets/icons",
    "design/mockups/web",
    "design/mockups/print",
    "design/templates/old",
    "legal/brand_usage",
    "finance/reports",
    "hr/onboarding",
    "product/roadmap",
    "comms/press_releases",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "marketing/campaigns/q3_launch/brief.txt": "Q3 Launch campaign brief. Product: Claude 3.5. Target: enterprise.",
    "marketing/campaigns/q3_launch/timeline.csv": "Phase,Start,End\nTeasing,2024-06-01,2024-06-15\nLaunch,2024-06-16,2024-06-30",
    "marketing/campaigns/q4_planning/ideas.txt": "Ideas for Q4: webinar series, case studies, partner co-marketing.",
    "marketing/assets/logos/usage_notes.txt": "Use SVG logos wherever possible. Minimum size: 32px height.",
    "marketing/assets/icons/icon_list.txt": "ai-chip.svg, cloud-sync.svg, safety-shield.svg, research-flask.svg",
    "design/mockups/web/homepage_notes.txt": "Hero section: dark background, light text. CTA button: orange accent.",
    "design/mockups/print/brochure_spec.txt": "Bleed: 3mm. CMYK output required for print vendor.",
    "design/templates/old/legacy_colors.txt": "OLD COLORS (deprecated): primary=#003366, secondary=#FF9900, text=#333333",
    "legal/brand_usage/trademark_notes.txt": "Anthropic(R) is a registered trademark. Always use correct capitalization.",
    "finance/reports/q2_summary.txt": "Q2 revenue summary placeholder. See finance dashboard for details.",
    "hr/onboarding/welcome_packet.txt": "Welcome to Anthropic! This packet covers your first week.",
    "product/roadmap/features_2024.txt": "Upcoming: improved context window, tool use enhancements, vision APIs.",
    "comms/press_releases/draft_launch.txt": "FOR IMMEDIATE RELEASE: Anthropic announces new product capabilities...",
    "design/templates/old/font_guide_old.txt": "OLD FONTS: Helvetica for headings, Times New Roman for body. (deprecated)",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the raw, unbranded PowerPoint that needs to be branded ---
# This file uses wrong colors and wrong fonts, simulating a "before" state.
prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)

slide_layouts = prs.slide_layouts

# ---- Slide 1: Title slide (wrong colors, no brand fonts) ----
slide1 = prs.slides.add_slide(slide_layouts[6])  # blank layout

# Background fill - wrong color (corporate blue, not brand dark)
from pptx.util import Inches, Pt
from pptx.oxml.ns import qn
from lxml import etree

def set_slide_background(slide, hex_color):
    """Set solid background color on a slide."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor.from_string(hex_color)

set_slide_background(slide1, "003366")  # wrong blue, not brand color

# Title text box - big heading, wrong font (Helvetica), wrong color
txBox = slide1.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(2))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Product Launch: Claude for Enterprise"
p.font.size = Pt(40)
p.font.name = "Helvetica"
p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
p.font.bold = True

# Subtitle - wrong font (Times New Roman), wrong color
txBox2 = slide1.shapes.add_textbox(Inches(1), Inches(4), Inches(11), Inches(1))
tf2 = txBox2.text_frame
p2 = tf2.paragraphs[0]
p2.text = "Transforming enterprise workflows with safe, powerful AI"
p2.font.size = Pt(20)
p2.font.name = "Times New Roman"
p2.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)

# Decorative rectangle (non-text shape) - wrong color
from pptx.util import Inches
rect1 = slide1.shapes.add_shape(
    1,  # MSO_SHAPE_TYPE.RECTANGLE
    Inches(1), Inches(6.5), Inches(11), Inches(0.3)
)
rect1.fill.solid()
rect1.fill.fore_color.rgb = RGBColor(0xFF, 0x99, 0x00)  # wrong orange
rect1.line.fill.background()

# ---- Slide 2: Content slide (agenda) ----
slide2 = prs.slides.add_slide(slide_layouts[6])
set_slide_background(slide2, "f0f0f0")  # wrong light gray

# Section heading - wrong font
txBox3 = slide2.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1.2))
tf3 = txBox3.text_frame
p3 = tf3.paragraphs[0]
p3.text = "Agenda"
p3.font.size = Pt(36)
p3.font.name = "Helvetica"
p3.font.bold = True
p3.font.color.rgb = RGBColor(0x00, 0x33, 0x66)  # wrong

# Body text - wrong font
body_items = [
    "1. Market Opportunity & Positioning",
    "2. Product Capabilities Overview",
    "3. Customer Success Stories",
    "4. Pricing & Packaging",
    "5. Go-to-Market Strategy",
]
txBox4 = slide2.shapes.add_textbox(Inches(1), Inches(1.8), Inches(10), Inches(4))
tf4 = txBox4.text_frame
tf4.word_wrap = True
for i, item in enumerate(body_items):
    if i == 0:
        p_item = tf4.paragraphs[0]
    else:
        p_item = tf4.add_paragraph()
    p_item.text = item
    p_item.font.size = Pt(18)
    p_item.font.name = "Times New Roman"
    p_item.font.color.rgb = RGBColor(0x33, 0x33, 0x33)  # wrong dark

# Two decorative shapes (non-text) - wrong colors
rect2 = slide2.shapes.add_shape(1, Inches(0.3), Inches(0.3), Inches(0.15), Inches(6.8))
rect2.fill.solid()
rect2.fill.fore_color.rgb = RGBColor(0x00, 0x33, 0x66)  # wrong
rect2.line.fill.background()

circle1 = slide2.shapes.add_shape(
    9,  # oval
    Inches(11.5), Inches(5.5), Inches(1.2), Inches(1.2)
)
circle1.fill.solid()
circle1.fill.fore_color.rgb = RGBColor(0xFF, 0x99, 0x00)  # wrong
circle1.line.fill.background()

# ---- Slide 3: Data/stats slide ----
slide3 = prs.slides.add_slide(slide_layouts[6])
set_slide_background(slide3, "141413")  # happens to be correct dark - test if agent preserves it

# Heading
txBox5 = slide3.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1.2))
tf5 = txBox5.text_frame
p5 = tf5.paragraphs[0]
p5.text = "Key Performance Metrics"
p5.font.size = Pt(32)
p5.font.name = "Helvetica"
p5.font.bold = True
p5.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)  # wrong light

# Subheading (borderline size - 22pt, below 24pt threshold, so should get Lora)
txBox6 = slide3.shapes.add_textbox(Inches(0.5), Inches(1.6), Inches(12), Inches(0.8))
tf6 = txBox6.text_frame
p6 = tf6.paragraphs[0]
p6.text = "Q3 2024 Results vs. Targets"
p6.font.size = Pt(22)
p6.font.name = "Helvetica"
p6.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

# Stats body text
stats = [
    "Enterprise Customers: 1,240 (+38% YoY)",
    "API Calls Processed: 2.8B per month",
    "Average Response Latency: 320ms",
    "Customer Satisfaction Score: 4.7/5.0",
    "Revenue Growth: 127% YoY",
]
txBox7 = slide3.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(12), Inches(4))
tf7 = txBox7.text_frame
tf7.word_wrap = True
for i, stat in enumerate(stats):
    if i == 0:
        p_stat = tf7.paragraphs[0]
    else:
        p_stat = tf7.add_paragraph()
    p_stat.text = stat
    p_stat.font.size = Pt(16)
    p_stat.font.name = "Times New Roman"
    p_stat.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)

# Three decorative shapes (to test accent color cycling across slides)
tri = slide3.shapes.add_shape(
    5,  # right triangle
    Inches(11.5), Inches(0.3), Inches(1.5), Inches(1.5)
)
tri.fill.solid()
tri.fill.fore_color.rgb = RGBColor(0x00, 0x33, 0x66)  # wrong
tri.line.fill.background()

# ---- Slide 4: Call to action slide ----
slide4 = prs.slides.add_slide(slide_layouts[6])
set_slide_background(slide4, "d97757")  # wrong - using accent as background

# Heading
txBox8 = slide4.shapes.add_textbox(Inches(1.5), Inches(2), Inches(10), Inches(1.5))
tf8 = txBox8.text_frame
p8 = tf8.paragraphs[0]
p8.text = "Get Started Today"
p8.font.size = Pt(44)
p8.font.name = "Helvetica"
p8.font.bold = True
p8.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

# Body
txBox9 = slide4.shapes.add_textbox(Inches(1.5), Inches(3.8), Inches(10), Inches(1))
tf9 = txBox9.text_frame
p9 = tf9.paragraphs[0]
p9.text = "Contact your Anthropic account team to schedule a pilot program"
p9.font.size = Pt(18)
p9.font.name = "Times New Roman"
p9.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

# Two decorative rectangles
rect3 = slide4.shapes.add_shape(1, Inches(1.5), Inches(5.2), Inches(4.5), Inches(0.8))
rect3.fill.solid()
rect3.fill.fore_color.rgb = RGBColor(0x00, 0x33, 0x66)  # wrong
rect3.line.fill.background()

rect4 = slide4.shapes.add_shape(1, Inches(7.3), Inches(5.2), Inches(4.5), Inches(0.8))
rect4.fill.solid()
rect4.fill.fore_color.rgb = RGBColor(0x00, 0x66, 0x00)  # wrong
rect4.line.fill.background()

# Save the unbranded presentation
output_path = os.path.join(workspace, "marketing/campaigns/q3_launch/product_launch_draft.pptx")
prs.save(output_path)

print(f"Generated unbranded presentation at: {output_path}")
print("Workspace structure created with distractor files.")
print("\nSummary of non-brand issues in the draft:")
print("- Wrong background colors (corporate blue, wrong grays, accent-as-background)")
print("- Wrong fonts (Helvetica for headings, Times New Roman for body)")
print("- Wrong accent colors on shapes (corporate blue, wrong orange, wrong green)")
print("- Text colors not following brand palette")