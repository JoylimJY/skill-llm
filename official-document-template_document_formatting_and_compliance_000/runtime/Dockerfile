FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN pip install python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the official-document-template script directory
RUN mkdir -p /root/.openclaw/workspace/official-document-template/scripts

# Write the conversion script
RUN cat > /root/.openclaw/workspace/official-document-template/scripts/convert_to_docx.py << 'PYEOF'
#!/usr/bin/env python3
"""
GB/T 9704-2012 Official Document Converter
Converts Markdown-formatted official documents to Word format.
"""
import sys
import re
import argparse
from pathlib import Path
from docx import Document
from docx.shared import Pt, Mm, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_font(run, font_name, size_pt, bold=False):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    r = run._r
    rPr = r.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:eastAsia'), font_name)
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    existing = rPr.find(qn('w:rFonts'))
    if existing is not None:
        rPr.remove(existing)
    rPr.insert(0, rFonts)

def set_line_spacing(paragraph, spacing_pt):
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    pPr = paragraph._p.get_or_add_pPr()
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:line'), str(int(spacing_pt * 20)))
    spacing.set(qn('w:lineRule'), 'exact')
    existing = pPr.find(qn('w:spacing'))
    if existing is not None:
        pPr.remove(existing)
    pPr.append(spacing)

def set_indent(paragraph, chars=2, font_size_pt=16):
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    indent_twips = int(chars * font_size_pt * 20)
    pPr = paragraph._p.get_or_add_pPr()
    ind = OxmlElement('w:ind')
    ind.set(qn('w:firstLine'), str(indent_twips))
    existing = pPr.find(qn('w:ind'))
    if existing is not None:
        pPr.remove(existing)
    pPr.append(ind)

def detect_heading_level(line):
    """Detect heading level based on GB/T 9704-2012 numbering conventions."""
    line = line.strip()
    # Level 1: 一、二、三、
    if re.match(r'^[一二三四五六七八九十]+、', line):
        return 1, line
    # Level 2: （一）（二）
    if re.match(r'^（[一二三四五六七八九十]+）', line):
        return 2, line
    # Level 3: 1. 2. 3.
    if re.match(r'^\d+\.', line):
        return 3, line
    # Level 4: （1）（2）
    if re.match(r'^（\d+）', line):
        return 4, line
    # Level 5: ①②③
    if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', line):
        return 5, line
    return 0, line

def convert_md_to_docx(input_path, output_path):
    doc = Document()
    
    # Set page size and margins (GB/T 9704-2012)
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(37)
    section.bottom_margin = Mm(35)
    section.left_margin = Mm(28)
    section.right_margin = Mm(26)

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Handle markdown H1 as document title (小标宋/黑体, centered)
        if stripped.startswith('# ') and not stripped.startswith('## '):
            title_text = stripped[2:].strip()
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(title_text)
            set_font(run, '黑体', 22, bold=False)
            set_line_spacing(para, 28)
            continue

        level, content = detect_heading_level(stripped)
        
        if level == 1:
            para = doc.add_paragraph()
            run = para.add_run(content)
            set_font(run, '黑体', 16, bold=False)
            set_line_spacing(para, 28)
            set_indent(para, 2, 16)
        elif level == 2:
            para = doc.add_paragraph()
            run = para.add_run(content)
            set_font(run, '楷体', 16, bold=True)
            set_line_spacing(para, 28)
            set_indent(para, 2, 16)
        elif level == 3:
            para = doc.add_paragraph()
            run = para.add_run(content)
            set_font(run, '仿宋', 16, bold=True)
            set_line_spacing(para, 28)
            set_indent(para, 2, 16)
        elif level == 4:
            para = doc.add_paragraph()
            run = para.add_run(content)
            set_font(run, '仿宋', 16, bold=False)
            set_line_spacing(para, 28)
            set_indent(para, 2, 16)
        elif level == 5:
            para = doc.add_paragraph()
            run = para.add_run(content)
            set_font(run, '仿宋', 16, bold=False)
            set_line_spacing(para, 28)
            set_indent(para, 2, 16)
        else:
            # Regular body text
            para = doc.add_paragraph()
            run = para.add_run(content)
            set_font(run, '仿宋', 16, bold=False)
            set_line_spacing(para, 28)
            set_indent(para, 2, 16)

    doc.save(output_path)
    print(f"Document saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Convert Markdown to GB/T 9704-2012 compliant Word document')
    parser.add_argument('input', help='Input Markdown file path')
    parser.add_argument('--output', required=True, help='Output Word document path')
    args = parser.parse_args()
    
    convert_md_to_docx(args.input, args.output)

if __name__ == '__main__':
    main()
PYEOF

RUN chmod +x /root/.openclaw/workspace/official-document-template/scripts/convert_to_docx.py

WORKDIR /workspace