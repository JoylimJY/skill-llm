#!/usr/bin/env python3
"""
Generate the sandbox workspace for the NotebookLM PDF Cleaner eval task.
Creates a realistic consulting-firm directory structure with distractors,
then generates a synthetic PDF that mimics a NotebookLM slide-deck export
with a footer badge, but at a non-standard page size (Letter portrait).
Also pre-creates a stale output file at the target path to trigger the
--force safety check.
"""

import os
import random
import struct
import zlib
from pathlib import Path

# ── reproducibility ──────────────────────────────────────────────────────────
random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

# ── directory skeleton (distractor files) ────────────────────────────────────
dirs = [
    "projects/acme-corp/decks",
    "projects/acme-corp/raw_exports",
    "projects/acme-corp/client_ready",
    "projects/beta-initiative/slides",
    "projects/beta-initiative/notes",
    "internal/templates",
    "internal/brand_assets",
    "archive/2023/q4",
    "archive/2024/q1",
    "tools/configs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# distractor text files
distractors = [
    ("projects/acme-corp/decks/meeting_notes.txt",          "Q3 strategy discussion notes\n- Revenue targets\n- Headcount"),
    ("projects/acme-corp/decks/agenda.md",                  "# Agenda\n1. Introductions\n2. Strategy\n3. Q&A"),
    ("projects/acme-corp/raw_exports/export_log.csv",       "timestamp,file,status\n2024-01-10,deck_v1.pdf,ok"),
    ("projects/beta-initiative/notes/brainstorm.txt",       "Ideas:\n- AI-powered analytics\n- Real-time dashboards"),
    ("projects/beta-initiative/slides/placeholder.txt",     "Slides pending client approval"),
    ("internal/templates/slide_template.pptx.bak",          "BINARY_PLACEHOLDER"),
    ("internal/brand_assets/colors.json",                   '{"primary":"#1A2B3C","accent":"#FF6B35"}'),
    ("archive/2023/q4/final_report.txt",                    "Annual report Q4 2023 - CONFIDENTIAL"),
    ("archive/2024/q1/deck_backup.txt",                     "Backup reference - deck sent 2024-01-15"),
    ("tools/configs/pdf_settings.ini",                      "[pdf]\ncompression=true\ndpi=150"),
    ("projects/acme-corp/client_ready/.gitkeep",            ""),
]
for rel, content in distractors:
    p = WORKSPACE / rel
    p.write_text(content)

# ── build the synthetic NotebookLM-style PDF using PyMuPDF ───────────────────
# Page size: US Letter portrait = 612 x 792 pt  (NOT the default 16:9 1376x774)
import fitz  # PyMuPDF

PAGE_W = 612   # Letter width  in points
PAGE_H = 792   # Letter height in points

def make_notebooklm_pdf(out_path: Path, num_pages: int = 4):
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=PAGE_W, height=PAGE_H)

        # Slide background — light grey
        page.draw_rect(fitz.Rect(0, 0, PAGE_W, PAGE_H),
                       color=(0.95, 0.95, 0.95), fill=(0.95, 0.95, 0.95))

        # Slide title
        page.insert_text(
            (40, 80),
            f"Acme Corp Strategy Deck — Slide {i+1}",
            fontsize=22,
            color=(0.1, 0.1, 0.4),
        )

        # Body text
        body_lines = [
            "• Market expansion in APAC region",
            "• Q2 revenue +18 % YoY",
            "• Headcount target: 240 FTE by EOY",
            "• AI-assisted workflow rollout",
        ]
        for j, line in enumerate(body_lines):
            page.insert_text((60, 160 + j * 40), line, fontsize=14, color=(0.2, 0.2, 0.2))

        # ── NotebookLM footer badge (bottom-right) ───────────────────────────
        # On a Letter page (612×792) the badge sits at bottom-right.
        # In PDF coordinates (origin=bottom-left):
        #   badge right edge  ~ page_w        = 612
        #   badge bottom edge ~               = 0  (very bottom)
        #   badge width       ~ proportional  = 168 * (612/1376) ≈ 74.7 → use 75
        #   badge height      ~ proportional  = 32  * (792/774)  ≈ 32.7 → use 33
        # In PyMuPDF rect coords (origin=top-left, y increases downward):
        #   top    = PAGE_H - badge_h_pt   ≈ 792 - 33 = 759
        #   bottom = PAGE_H               = 792
        #   left   = PAGE_W  - badge_w_pt ≈ 612 - 75 = 537
        #   right  = PAGE_W               = 612
        badge_rect = fitz.Rect(537, 759, 612, 792)
        page.draw_rect(badge_rect, color=(0.2, 0.4, 0.8), fill=(0.2, 0.4, 0.8))
        page.insert_text(
            (540, 780),
            "NotebookLM",
            fontsize=7,
            color=(1.0, 1.0, 1.0),
        )

    # embed some metadata to test --strip-metadata
    doc.set_metadata({
        "title":    "Acme Corp Q2 Strategy",
        "author":   "NotebookLM AI",
        "subject":  "Internal strategy deck",
        "creator":  "NotebookLM/1.0",
        "producer": "NotebookLM PDF Export",
        "keywords": "confidential, internal",
    })

    doc.save(str(out_path))
    doc.close()

input_pdf = WORKSPACE / "projects/acme-corp/raw_exports/acme_q2_strategy.pdf"
make_notebooklm_pdf(input_pdf, num_pages=4)
print(f"[gen_inputs] Created input PDF: {input_pdf}")

# ── pre-create a STALE output file at the exact target path ──────────────────
# This forces the agent to use --force (safety check in SKILL.md)
stale_output = WORKSPACE / "projects/acme-corp/client_ready/acme_q2_strategy_final.pdf"
stale_output.write_bytes(b"%PDF-1.4 stale placeholder - do not send to client\n")
print(f"[gen_inputs] Created stale output file: {stale_output}")

print("[gen_inputs] Workspace generation complete.")