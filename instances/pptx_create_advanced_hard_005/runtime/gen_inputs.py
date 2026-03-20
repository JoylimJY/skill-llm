#!/usr/bin/env python3
import os
import json
from pathlib import Path

# Create marker content for verification
marker_data = {
    "company_name": "TechFlow Solutions",
    "quarter": "Q3 2024",
    "revenue_growth": 23,
    "churn_rate": 2.1,
    "new_customers": 450,
    "theme_color": "1E2761",
    "accent_color": "028090",
    "required_slides": [
        "title",
        "executive_summary", 
        "financial_performance",
        "product_roadmap",
        "team_highlights",
        "customer_testimonials",
        "competitive_analysis",
        "next_steps"
    ],
    "testimonial_customers": ["Acme Corp", "Global Systems", "InnovateTech"],
    "team_members": ["Sarah Chen - VP Product", "Mike Rodriguez - CTO", "Lisa Zhang - Head of Sales"],
    "roadmap_features": ["AI Analytics Dashboard", "Mobile App V2", "Enterprise SSO", "Advanced Reporting"]
}

# Save marker data for eval verification
with open('expected_content.json', 'w') as f:
    json.dump(marker_data, f, indent=2)

# Create sample team photos as placeholder images (1x1 colored squares)
from PIL import Image

colors = [(70, 130, 180), (220, 20, 60), (34, 139, 34)]  # Steel blue, crimson, forest green
for i, color in enumerate(colors, 1):
    img = Image.new('RGB', (256, 256), color)
    img.save(f'team_photo_{i}.png')

print("Generated input files with marker content for QBR presentation task")
