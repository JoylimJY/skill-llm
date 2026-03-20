#!/usr/bin/env python3
import json
import csv
import random
from pathlib import Path
from docx import Document
from pptx import Presentation
from pptx.util import Inches
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

# Set deterministic seed
random.seed(42)

# Create overview.txt
with open('overview.txt', 'w') as f:
    f.write('''GreenTech Solutions: Revolutionizing Sustainable Energy Storage

COMPANY_MARKER_12345: Our mission is to accelerate the world's transition to sustainable energy through innovative battery technology.

Problem Statement:
Current lithium-ion batteries suffer from limited lifespan, safety concerns, and environmental impact. The market needs a breakthrough solution that addresses these critical issues while maintaining cost-effectiveness.

Solution Overview:
GreenTech has developed proprietary solid-state battery technology that delivers 3x longer lifespan, 50% faster charging, and zero fire risk. Our patented electrolyte formula uses abundant materials, reducing dependency on rare earth elements.

Business Model:
We license our technology to major manufacturers while producing specialty applications in-house. Revenue streams include licensing fees, royalties, and direct sales of premium battery packs.

Funding Ask:
Seeking $15M Series A to scale manufacturing, complete automotive certifications, and expand our engineering team. This will position us to capture significant market share in the rapidly growing energy storage sector.''')

# Create quarterly_data.csv
with open('quarterly_data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Quarter', 'Revenue_Millions', 'Market_Size_Billions', 'Market_Share_Percent'])
    writer.writerow(['Q1 2023', '2.1', '45.2', '0.8'])
    writer.writerow(['Q2 2023', '3.5', '48.7', '1.2'])
    writer.writerow(['Q3 2023', '5.2', '52.1', '1.8'])
    writer.writerow(['Q4 2023', '7.8', '55.9', '2.4'])
    writer.writerow(['Q1 2024', '11.2', '60.2', '3.1'])
    writer.writerow(['FINANCIAL_MARKER_67890', '15.8', '64.8', '4.2'])

# Create team_profiles.json
team_data = {
    "TEAM_MARKER_54321": "executive_profiles",
    "team_members": [
        {
            "name": "Dr. Sarah Chen",
            "title": "CEO & Co-Founder",
            "bio": "Former Tesla battery engineer with 15 years experience. PhD in Materials Science from MIT. Led development of Model S battery pack.",
            "photo": "sarah_chen.jpg"
        },
        {
            "name": "Marcus Rodriguez",
            "title": "CTO & Co-Founder",
            "bio": "Ex-Google X researcher specializing in energy storage. MS in Chemical Engineering from Stanford. 12 patents in battery technology.",
            "photo": "marcus_rodriguez.jpg"
        },
        {
            "name": "Jennifer Park",
            "title": "VP of Operations",
            "bio": "Former manufacturing director at Panasonic. Expert in scaling battery production. MBA from Wharton.",
            "photo": "jennifer_park.jpg"
        }
    ]
}
with open('team_profiles.json', 'w') as f:
    json.dump(team_data, f, indent=2)

# Create market_research.docx
doc = Document()
doc.add_heading('Energy Storage Market Analysis 2024', 0)

para = doc.add_paragraph()
para.add_run('MARKET_MARKER_98765: ').bold = True
para.add_run('The global energy storage market is experiencing unprecedented growth.')

doc.add_heading('Market Opportunity', level=1)
doc.add_paragraph('The energy storage market is projected to reach $120 billion by 2026, driven by renewable energy adoption and electric vehicle demand. Key growth segments include grid-scale storage (40% CAGR) and automotive applications (35% CAGR).')

doc.add_heading('Competitive Landscape', level=1) 
doc.add_paragraph('Current market leaders include Tesla/Panasonic (25% market share), CATL (20%), and LG Energy (15%). However, these players rely on legacy lithium-ion technology with inherent limitations. Our solid-state solution represents a generational leap that can disrupt established players.')

doc.add_paragraph('Key competitive advantages: 3x longer cycle life, 2x energy density, zero thermal runaway risk, and 50% reduction in rare earth material usage.')

doc.save('market_research.docx')

# Create corporate_template.pptx
pres = Presentation()
pres.slide_width = Inches(16)
pres.slide_height = Inches(9)

# Title slide with placeholder
slide_layout = pres.slide_layouts[0]  # Title slide
slide = pres.slides.add_slide(slide_layout)
title = slide.shapes.title
subtitle = slide.placeholders[1]
title.text = "XXXX Company Presentation XXXX"
subtitle.text = "TEMPLATE_MARKER_11111: Replace with actual content"

# Content slide with bullet points
slide_layout = pres.slide_layouts[1]  # Title and content
slide = pres.slides.add_slide(slide_layout)
title = slide.shapes.title
content = slide.placeholders[1]
title.text = "Key Points Template"
tf = content.text_frame
tf.text = "PLACEHOLDER_MARKER_22222: First key point"
p = tf.add_paragraph()
p.text = "Second key point placeholder"
p.level = 0
p = tf.add_paragraph()
p.text = "Third key point placeholder" 
p.level = 0

# Two-column layout slide
slide_layout = pres.slide_layouts[3]  # Title and two content
slide = pres.slides.add_slide(slide_layout)
title = slide.shapes.title
left_content = slide.placeholders[1] 
right_content = slide.placeholders[2]
title.text = "Two Column Layout"
left_content.text = "Left column content placeholder"
right_content.text = "Right column content placeholder"

# Section header slide
slide_layout = pres.slide_layouts[2]  # Section header
slide = pres.slides.add_slide(slide_layout) 
title = slide.shapes.title
title.text = "SECTION_MARKER_33333: Section Title"

# Blank slide for charts
slide_layout = pres.slide_layouts[6]  # Blank
slide = pres.slides.add_slide(slide_layout)
textbox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1))
tf = textbox.text_frame
tf.text = "CHART_MARKER_44444: Financial data visualization will go here"

pres.save('corporate_template.pptx')

print("Generated input files with embedded markers for verification")