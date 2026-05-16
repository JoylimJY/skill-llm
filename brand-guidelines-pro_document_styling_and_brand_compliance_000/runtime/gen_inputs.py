import os
import random
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

random.seed(42)

BASE = "/workspace"

# --- Create realistic distractor directory structure ---
dirs = [
    "marketing/assets/logos",
    "marketing/assets/icons",
    "marketing/campaigns/q3_2024",
    "marketing/campaigns/q4_2024",
    "design/mockups",
    "design/templates/old",
    "design/templates/draft",
    "finance/reports",
    "finance/forecasts",
    "hr/onboarding",
    "hr/policies",
    "engineering/docs",
    "engineering/specs",
    "product/roadmap",
    "product/research",
    "legal/contracts",
    "legal/compliance",
    "ops/workflows",
    "ops/runbooks",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# Distractor files
distractor_files = {
    "marketing/assets/brand_overview.txt": "Old brand guide - DEPRECATED. Colors: red #ff0000, blue #0000ff.",
    "marketing/assets/logos/logo_usage.txt": "Use logo on white background only. Minimum size: 50px.",
    "marketing/campaigns/q3_2024/campaign_brief.md": "# Q3 Campaign\nTarget: Enterprise\nBudget: $500k\nKPIs: 200 leads",
    "marketing/campaigns/q4_2024/messaging_matrix.csv": "Segment,Message,Channel\nEnterprise,Safety+Scale,LinkedIn\nSMB,Ease of use,Email",
    "design/mockups/homepage_v1.txt": "Placeholder: Homepage wireframe notes.",
    "design/mockups/homepage_v2.txt": "Placeholder: Updated homepage wireframe.",
    "design/templates/old/legacy_template_notes.txt": "Legacy template uses Helvetica and blue #003366. DO NOT USE.",
    "design/templates/draft/draft_style_guide.txt": "Draft only. Fonts: Open Sans. Colors: TBD.",
    "finance/reports/q2_revenue.csv": "Month,Revenue\nApr,1200000\nMay,1350000\nJun,1480000",
    "finance/forecasts/fy2025_forecast.txt": "FY2025 projected ARR: $45M. Growth rate: 35%.",
    "hr/onboarding/welcome_packet.txt": "Welcome to Anthropic! Please complete your onboarding checklist.",
    "hr/policies/pto_policy.txt": "PTO Policy: 20 days per year. Rollover cap: 10 days.",
    "engineering/docs/api_reference.txt": "API v2 reference. Endpoint: /v1/messages. Method: POST.",
    "engineering/specs/architecture_diagram.txt": "Microservices arch. Services: auth, inference, billing.",
    "product/roadmap/q4_roadmap.md": "# Q4 Roadmap\n- Feature A: Oct\n- Feature B: Nov\n- Feature C: Dec",
    "product/research/user_interviews.txt": "User interview themes: speed, reliability, pricing.",
    "legal/contracts/vendor_template.txt": "Standard vendor agreement template. Version 3.2.",
    "legal/compliance/gdpr_checklist.txt": "GDPR checklist items: DPA signed, data mapping done.",
    "ops/workflows/release_process.md": "# Release Process\n1. Code freeze\n2. QA\n3. Deploy\n4. Monitor",
    "ops/runbooks/incident_response.txt": "Incident response: 1. Detect 2. Alert 3. Mitigate 4. Postmortem",
}
for path, content in distractor_files.items():
    full_path = os.path.join(BASE, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the actual messy PowerPoint that needs rebranding ---
# This deck uses totally wrong colors and fonts - needs Anthropic branding applied

prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)

slide_layout = prs.slide_layouts[6]  # Blank layout

# ---- SLIDE 1: Title slide with wrong colors ----
slide1 = prs.slides.add_slide(slide_layout)

# Wrong background - bright red
bg = slide1.background
fill = bg.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0xFF, 0x00, 0x00)  # Wrong: red

# Title text box - 40pt heading - wrong font (Helvetica) and wrong color
from pptx.util import Inches, Pt, Emu
txBox = slide1.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(1.5))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
run = p.add_run()
run.text = "Anthropic Quarterly Business Review"
run.font.size = Pt(40)
run.font.name = "Helvetica"  # Wrong font
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0x00)  # Wrong: yellow
run.font.bold = True

# Subtitle - 18pt body text - wrong font
txBox2 = slide1.shapes.add_textbox(Inches(2), Inches(3.8), Inches(9), Inches(1))
tf2 = txBox2.text_frame
p2 = tf2.paragraphs[0]
p2.alignment = PP_ALIGN.CENTER
run2 = p2.add_run()
run2.text = "Q4 2024 | Prepared by Marketing & Strategy"
run2.font.size = Pt(18)
run2.font.name = "Comic Sans MS"  # Wrong font
run2.font.color.rgb = RGBColor(0x00, 0x80, 0x00)  # Wrong: green

# A decorative shape - should get accent color
shape1 = slide1.shapes.add_shape(
    1,  # MSO_SHAPE_TYPE.RECTANGLE
    Inches(0), Inches(6.8), Inches(13.33), Inches(0.7)
)
shape1.fill.solid()
shape1.fill.fore_color.rgb = RGBColor(0x80, 0x00, 0x80)  # Wrong: purple
shape1.line.color.rgb = RGBColor(0x80, 0x00, 0x80)

# ---- SLIDE 2: Metrics slide ----
slide2 = prs.slides.add_slide(slide_layout)

bg2 = slide2.background
fill2 = bg2.fill
fill2.solid()
fill2.fore_color.rgb = RGBColor(0x00, 0x00, 0xFF)  # Wrong: blue bg

# Section heading - 28pt - wrong font
txBox3 = slide2.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
tf3 = txBox3.text_frame
p3 = tf3.paragraphs[0]
run3 = p3.add_run()
run3.text = "Key Performance Metrics"
run3.font.size = Pt(28)
run3.font.name = "Times New Roman"  # Wrong
run3.font.color.rgb = RGBColor(0xFF, 0xA5, 0x00)  # Wrong: orange

# Body bullet points - 16pt - wrong font
txBox4 = slide2.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(6), Inches(4))
tf4 = txBox4.text_frame
tf4.word_wrap = True

bullets = [
    ("Revenue Growth: +42% YoY", 16),
    ("Customer Satisfaction: 4.8/5.0", 16),
    ("API Uptime: 99.97%", 16),
    ("Enterprise Clients: 340 (+28%)", 16),
    ("Net Revenue Retention: 118%", 14),
]
for i, (text, size) in enumerate(bullets):
    if i == 0:
        p_bullet = tf4.paragraphs[0]
    else:
        p_bullet = tf4.add_paragraph()
    r = p_bullet.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.name = "Courier New"  # Wrong font
    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

# Three metric shapes - should cycle accent colors
for i, (label, val) in enumerate([("ARR", "$38M"), ("NPS", "72"), ("Churn", "1.2%")]):
    box = slide2.shapes.add_shape(
        1,
        Inches(7.5 + i * 1.8), Inches(1.5), Inches(1.5), Inches(1.5)
    )
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0x80, 0x80, 0x80)  # Wrong: gray
    box.line.color.rgb = RGBColor(0x80, 0x80, 0x80)

# ---- SLIDE 3: Strategy slide ----
slide3 = prs.slides.add_slide(slide_layout)

bg3 = slide3.background
fill3 = bg3.fill
fill3.solid()
fill3.fore_color.rgb = RGBColor(0x33, 0x33, 0x33)  # Slightly wrong dark

# Main heading - 32pt
txBox5 = slide3.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
tf5 = txBox5.text_frame
p5 = tf5.paragraphs[0]
run5 = p5.add_run()
run5.text = "Strategic Priorities for 2025"
run5.font.size = Pt(32)
run5.font.name = "Georgia"  # Wrong for heading
run5.font.color.rgb = RGBColor(0x00, 0xFF, 0xFF)  # Wrong: cyan

# Sub-heading - 24pt (boundary case - exactly 24pt = heading)
txBox6 = slide3.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(12), Inches(0.8))
tf6 = txBox6.text_frame
p6 = tf6.paragraphs[0]
run6 = p6.add_run()
run6.text = "Safety & Scalability Roadmap"
run6.font.size = Pt(24)
run6.font.name = "Arial"  # Should become Poppins
run6.font.color.rgb = RGBColor(0xFF, 0x00, 0xFF)  # Wrong: magenta

# Body text - 14pt
txBox7 = slide3.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(11), Inches(3.5))
tf7 = txBox7.text_frame
tf7.word_wrap = True
strategy_text = [
    "1. Expand Constitutional AI research across all model families",
    "2. Scale inference infrastructure to support 10x user growth",
    "3. Launch enterprise compliance and audit tooling suite",
    "4. Deepen partnerships with safety-focused academic institutions",
    "5. Develop next-generation alignment evaluation benchmarks",
]
for i, line in enumerate(strategy_text):
    if i == 0:
        pp = tf7.paragraphs[0]
    else:
        pp = tf7.add_paragraph()
    rr = pp.add_run()
    rr.text = line
    rr.font.size = Pt(14)
    rr.font.name = "Verdana"  # Wrong
    rr.font.color.rgb = RGBColor(0xFF, 0xCC, 0x00)  # Wrong: yellow

# Two accent shapes on slide 3
for i in range(2):
    s = slide3.shapes.add_shape(
        1,
        Inches(0.5 + i * 6.5), Inches(6.2), Inches(6), Inches(0.5)
    )
    s.fill.solid()
    s.fill.fore_color.rgb = RGBColor(0x00, 0x66, 0x99)  # Wrong
    s.line.color.rgb = RGBColor(0x00, 0x66, 0x99)

# Save the problematic presentation
prs.save(os.path.join(BASE, "marketing/campaigns/q4_2024/qbr_deck_draft.pptx"))

print("Workspace generated successfully.")
print(f"Distractor files: {len(distractor_files)}")
print("PPTX created: marketing/campaigns/q4_2024/qbr_deck_draft.pptx")