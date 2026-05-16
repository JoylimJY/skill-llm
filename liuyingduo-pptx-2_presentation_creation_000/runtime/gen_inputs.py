#!/usr/bin/env python3
"""
Generate the sandbox workspace for the fintech investor pitch deck task.
Creates a realistic project structure with distractor files, raw content data,
and brand guidelines — but NO pre-built scripts or hints about the solution.
"""

import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ── Directory structure ─────────────────────────────────────────────────────
dirs = [
    "data",
    "brand",
    "research",
    "financials",
    "scripts/office",
    "scripts",
    "assets/icons",
    "assets/images",
    "notes",
    "old_decks",
    "competitor_analysis",
    "legal",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── MAIN TASK INPUT: Company brief JSON ─────────────────────────────────────
company_brief = {
    "company": "NexaPay",
    "tagline": "INSTANT  GLOBAL  PAYMENTS",
    "description": "NexaPay is a B2B fintech platform enabling cross-border payment settlement in under 3 seconds using distributed ledger technology.",
    "founded": 2021,
    "slides": [
        {
            "slide_number": 1,
            "type": "title",
            "title": "NexaPay",
            "subtitle": "Redefining Cross-Border Payments for the Modern Enterprise",
            "tagline_note": "Display the tagline text with wide character spacing for visual impact"
        },
        {
            "slide_number": 2,
            "type": "problem",
            "title": "The Problem",
            "points": [
                "Global B2B payments take 3-5 days to settle",
                "Average fee per transaction: 2.8% of value",
                "47% of CFOs cite payment delays as a top operational risk",
                "$120B lost annually to failed cross-border transactions"
            ]
        },
        {
            "slide_number": 3,
            "type": "solution",
            "title": "Our Solution",
            "features": [
                {"icon": "speed", "label": "3-Second Settlement", "desc": "Sub-3s finality on all corridors"},
                {"icon": "shield", "label": "Bank-Grade Security", "desc": "SOC 2 Type II certified"},
                {"icon": "globe", "label": "190+ Countries", "desc": "Full regulatory compliance"},
                {"icon": "chart", "label": "0.4% Flat Fee", "desc": "7x cheaper than legacy rails"}
            ]
        },
        {
            "slide_number": 4,
            "type": "traction",
            "title": "Traction",
            "chart": {
                "type": "bar",
                "title": "Monthly Transaction Volume (USD Millions)",
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "values": [1.2, 2.1, 3.8, 5.4, 8.9, 14.2]
            },
            "stats": [
                {"number": "$42M", "label": "Total Processed"},
                {"number": "380+", "label": "Enterprise Clients"},
                {"number": "3.2x", "label": "MoM Growth"}
            ]
        },
        {
            "slide_number": 5,
            "type": "closing",
            "title": "Join the Future of Payments",
            "ask": "Raising $12M Series A",
            "use_of_funds": [
                "40% — Engineering & Product",
                "35% — Sales & Marketing",
                "25% — Regulatory & Compliance"
            ],
            "contact": "invest@nexapay.io"
        }
    ],
    "brand": {
        "palette": "Ocean Gradient",
        "primary": "065A82",
        "secondary": "1C7293",
        "accent": "21295C",
        "background_title": "065A82",
        "background_content": "F8FAFC",
        "text_dark": "1E293B",
        "text_light": "FFFFFF"
    },
    "typography": {
        "header_font": "Georgia",
        "body_font": "Calibri",
        "title_size": 40,
        "header_size": 22,
        "body_size": 15
    },
    "output_filename": "nexapay_pitch.pptx"
}

with open(WORKSPACE / "data" / "company_brief.json", "w") as f:
    json.dump(company_brief, f, indent=2)

# ── Brand guidelines (distractor + useful color refs) ────────────────────────
brand_guide = """# NexaPay Brand Guidelines

## Colors
Primary: #065A82 (Deep Blue)
Secondary: #1C7293 (Teal)  
Accent: #21295C (Midnight)
Light BG: #F8FAFC
Dark Text: #1E293B

## Typography
Headers: Georgia
Body: Calibri

## Logo Usage
- Minimum size: 80px
- Clear space: 1x logo height on all sides

## Tone
Professional, confident, modern.
"""
(WORKSPACE / "brand" / "brand_guidelines.md").write_text(brand_guide)

# ── Research notes (distractors) ─────────────────────────────────────────────
research_notes = """# Market Research

## TAM/SAM/SOM
- TAM: $156B global B2B cross-border payments
- SAM: $23B addressable with current tech stack
- SOM: $1.2B in first 5 years

## Competitor Landscape
| Company | Settlement Time | Fee |
|---------|----------------|-----|
| SWIFT   | 3-5 days       | 3.5% |
| Wise    | 1-2 days       | 1.2% |
| NexaPay | <3 seconds     | 0.4% |

Source: McKinsey Global Payments Report 2024
"""
(WORKSPACE / "research" / "market_analysis.md").write_text(research_notes)

# ── Financial model CSV (distractor) ─────────────────────────────────────────
financial_csv = """Month,Volume_MUSD,Clients,Revenue_KUSD
Jan,1.2,45,4.8
Feb,2.1,78,8.4
Mar,3.8,121,15.2
Apr,5.4,189,21.6
May,8.9,264,35.6
Jun,14.2,380,56.8
"""
(WORKSPACE / "financials" / "monthly_metrics.csv").write_text(financial_csv)

# ── Old deck placeholder (distractor) ────────────────────────────────────────
(WORKSPACE / "old_decks" / "nexapay_v1_draft.txt").write_text(
    "Old draft - superseded. See data/company_brief.json for current content."
)

# ── Competitor analysis (distractor) ────────────────────────────────────────
(WORKSPACE / "competitor_analysis" / "swift_analysis.txt").write_text(
    "SWIFT: Founded 1973. 11,000+ member institutions. Primary weakness: batch processing model."
)
(WORKSPACE / "competitor_analysis" / "wise_analysis.txt").write_text(
    "Wise: Consumer-focused, not enterprise-grade. No API SLA guarantees."
)

# ── Legal docs (distractors) ─────────────────────────────────────────────────
(WORKSPACE / "legal" / "term_sheet_template.txt").write_text(
    "CONFIDENTIAL TERM SHEET\nIssuer: NexaPay Inc.\n[DRAFT - NOT FOR DISTRIBUTION]"
)

# ── Notes (distractors) ──────────────────────────────────────────────────────
(WORKSPACE / "notes" / "investor_meeting_notes.txt").write_text(
    "Meeting with Sequoia 2024-11-15\n- Ask about defensibility\n- Show traction chart\n- Emphasize regulatory moat"
)
(WORKSPACE / "notes" / "design_feedback.txt").write_text(
    "Feedback from CEO: 'Make it pop. Use the ocean blue palette. Add icons for features slide.'"
)

# ── Scripts stubs (real scripts exist, these are config/notes) ───────────────
(WORKSPACE / "scripts" / "README_scripts.txt").write_text(
    "office/ - packing/unpacking utilities\nadd_slide.py - duplicate slides\nclean.py - remove orphaned files\nthumbnail.py - visual grid"
)

# ── Assets placeholder ───────────────────────────────────────────────────────
(WORKSPACE / "assets" / "icons" / "icon_sources.txt").write_text(
    "Icons sourced from react-icons. Use FaBolt, FaShieldAlt, FaGlobe, FaChartLine from react-icons/fa"
)
(WORKSPACE / "assets" / "images" / "image_notes.txt").write_text(
    "Background images: use solid color fills from brand palette for this deck."
)

print(f"Workspace initialized at {WORKSPACE}")
print("Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")