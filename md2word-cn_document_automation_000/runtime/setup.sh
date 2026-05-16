#!/bin/bash
set -e

# Ensure the skill script is properly installed
SKILL_DIR="/root/.agents/skills/md2word-cn/scripts"
mkdir -p "$SKILL_DIR"

# Download the skill script from the known public location or reconstruct it
# The skill's md2word.py is expected to already exist per the SKILL.md contract.
# We install it fresh to guarantee determinism.

cat > "$SKILL_DIR/md2word.py" << 'PYEOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md2word-cn: Markdown to Word converter for Chinese documents.
Font: FangSong (仿宋) throughout.
"""

import sys
import re
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


FONT_NAME = "仿宋"


def set_font(run, size_pt, bold=False, italic=False, strike=False, underline=False, color=None):
    run.font.name = FONT_NAME
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    run.font.strike = strike
    run.font.underline = underline
    run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)
    if color:
        run.font.color.rgb = color


def add_paragraph_with_font(doc, text, size_pt, bold=False, italic=False,
                              align=WD_ALIGN_PARAGRAPH.LEFT, style=None):
    if style:
        p = doc.add_paragraph(style=style)
    else:
        p = doc.add_paragraph()
    p.alignment = align
    run = p.add_run(text)
    set_font(run, size_pt, bold=bold, italic=italic)
    return p


def parse_inline(paragraph, text, default_size=12):
    """Parse inline markdown: **bold**, *italic*, ~~strike~~, `code`, [link](url)"""
    pattern = r'(\*\*(.+?)\*\*|\*(.+?)\*|~~(.+?)~~|`(.+?)`|\[(.+?)\]\((.+?)\))'
    last = 0
    for m in re.finditer(pattern, text):
        # plain text before match
        if m.start() > last:
            run = paragraph.add_run(text[last:m.start()])
            set_font(run, default_size)
        full = m.group(0)
        if full.startswith('**'):
            run = paragraph.add_run(m.group(2))
            set_font(run, default_size, bold=True)
        elif full.startswith('*'):
            run = paragraph.add_run(m.group(3))
            set_font(run, default_size, italic=True)
        elif full.startswith('~~'):
            run = paragraph.add_run(m.group(4))
            set_font(run, default_size, strike=True)
        elif full.startswith('`'):
            run = paragraph.add_run(m.group(5))
            set_font(run, default_size)
            run.font.highlight_color = None
            # gray-ish via shading is complex; just set courier-style
            run.font.name = "Courier New"
            run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)
        elif full.startswith('['):
            run = paragraph.add_run(m.group(6))
            set_font(run, default_size, underline=True)
            run.font.color.rgb = RGBColor(0x00, 0x00, 0xFF)
        last = m.end()
    # remaining text
    if last < len(text):
        run = paragraph.add_run(text[last:])
        set_font(run, default_size)


def add_horizontal_rule(doc):
    p = doc.add_paragraph()
    pPr = p._element.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'auto')
    pBdr.append(bottom)
    pPr.append(pBdr)


def convert(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    doc = Document()
    # Remove default styles margin noise
    for section in doc.sections:
        section.top_margin = Pt(72)
        section.bottom_margin = Pt(72)
        section.left_margin = Pt(90)
        section.right_margin = Pt(90)

    in_code_block = False
    code_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip('\n')

        # Code block toggle
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lines = []
                i += 1
                continue
            else:
                in_code_block = False
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for cl in code_lines:
                    run = p.add_run(cl + '\n')
                    run.font.name = "Courier New"
                    run.font.size = Pt(10)
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)
                # gray background
                pPr = p._element.get_or_add_pPr()
                shd = OxmlElement('w:shd')
                shd.set(qn('w:val'), 'clear')
                shd.set(qn('w:color'), 'auto')
                shd.set(qn('w:fill'), 'F2F2F2')
                pPr.append(shd)
                i += 1
                continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Horizontal rule
        if stripped == '---':
            add_horizontal_rule(doc)
            i += 1
            continue

        # Headings
        h4 = re.match(r'^#### (.+)', line)
        h3 = re.match(r'^### (.+)', line)
        h2 = re.match(r'^## (.+)', line)
        h1 = re.match(r'^# (.+)', line)

        if h1:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(h1.group(1))
            set_font(run, 22, bold=True)
            i += 1
            continue
        if h2:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(h2.group(1))
            set_font(run, 16, bold=True)
            i += 1
            continue
        if h3:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(h3.group(1))
            set_font(run, 14, bold=True)
            i += 1
            continue
        if h4:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(h4.group(1))
            set_font(run, 12, bold=True)
            i += 1
            continue

        # Blockquote
        bq = re.match(r'^> (.+)', line)
        if bq:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            parse_inline(p, bq.group(1), default_size=12)
            # indent
            p.paragraph_format.left_indent = Pt(24)
            i += 1
            continue

        # Ordered list (manual numbering)
        ol = re.match(r'^(\d+)\. (.+)', line)
        if ol:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            parse_inline(p, ol.group(1) + '. ' + ol.group(2), default_size=12)
            p.paragraph_format.left_indent = Pt(24)
            i += 1
            continue

        # Unordered list
        ul = re.match(r'^[-*] (.+)', line)
        if ul:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            parse_inline(p, '• ' + ul.group(1), default_size=12)
            p.paragraph_format.left_indent = Pt(24)
            i += 1
            continue

        # Empty line
        if stripped == '':
            i += 1
            continue

        # Normal paragraph
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        parse_inline(p, stripped, default_size=12)
        i += 1

    doc.save(output_path)
    print(f"[md2word-cn] Saved: {output_path}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 md2word.py <input.md> <output.docx>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
PYEOF

chmod +x "$SKILL_DIR/md2word.py"
echo "[setup] md2word-cn skill installed at $SKILL_DIR/md2word.py"

# Create a symlink for convenience
mkdir -p /workspace/tools/converters
ln -sf "$SKILL_DIR/md2word.py" /workspace/tools/converters/md2word.py 2>/dev/null || true

echo "[setup] Setup complete."