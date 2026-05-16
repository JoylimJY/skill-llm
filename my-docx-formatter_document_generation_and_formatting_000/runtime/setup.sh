#!/bin/bash
set -e

SKILL_DIR="/root/.openclaw/workspace/skills/docx-formatter"
mkdir -p "$SKILL_DIR/examples"

# ── Write the main docx-formatter CLI script ─────────────────────────────────
cat > "$SKILL_DIR/docx-formatter" << 'PYEOF'
#!/usr/bin/env python3
"""
docx-formatter: 公文格式规范生成器
Generates Word documents strictly following Chinese official document format standards.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Cm, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.enum.section import WD_SECTION
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    import lxml.etree as etree
except ImportError:
    print("依赖缺失，请先运行 ./install.sh", file=sys.stderr)
    sys.exit(1)

# ── Font size constants (磅) ──────────────────────────────────────────────────
SIZE_2 = Pt(22)   # 2号 = 22pt
SIZE_3 = Pt(16)   # 3号 = 16pt

# ── Font names ────────────────────────────────────────────────────────────────
FONT_TITLE    = "方正小标宋简体"
FONT_H1       = "黑体"
FONT_H2       = "楷体_GB2312"
FONT_BODY     = "仿宋_GB2312"
FONT_H3_BODY  = "仿宋_GB2312"  # 三级标题同正文字体，加粗前缀

# ── Spacing ───────────────────────────────────────────────────────────────────
LINE_SPACING_PT = 28   # fixed 28pt
INDENT_PT       = 32   # first-line indent ~2 chars at 3号


def _set_font(run, name, size, bold=False):
    run.font.name = name
    run.font.size = size
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    # Force East Asian font
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), name)
    rFonts.set(qn('w:ascii'), name)
    rFonts.set(qn('w:hAnsi'), name)


def _set_paragraph_format(para, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                           first_line_indent=True, space_before=0, space_after=0):
    pf = para.paragraph_format
    pf.alignment = align
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(LINE_SPACING_PT)
    if first_line_indent:
        pf.first_line_indent = Pt(INDENT_PT)
    else:
        pf.first_line_indent = Pt(0)
    # Disable widow/orphan control
    pPr = para._p.get_or_add_pPr()
    wc = pPr.find(qn('w:widowControl'))
    if wc is None:
        wc = OxmlElement('w:widowControl')
        pPr.append(wc)
    wc.set(qn('w:val'), '0')


def _add_page_number(section):
    """Add centered page number in footer."""
    footer = section.footer
    footer.is_linked_to_previous = False
    for para in footer.paragraphs:
        para.clear()
    if not footer.paragraphs:
        para = footer.add_paragraph()
    else:
        para = footer.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.text = ' PAGE '
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)


def _normalize_quotes(text):
    """Replace straight quotes with Chinese curly quotes."""
    result = []
    open_q = True
    for ch in text:
        if ch == '"':
            result.append('\u201c' if open_q else '\u201d')
            open_q = not open_q
        else:
            result.append(ch)
    return ''.join(result)


def build_document(title, author, paragraphs_data):
    doc = Document()

    # ── Page setup ─────────────────────────────────────────────────────────
    section = doc.sections[0]
    section.page_width  = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin   = Inches(1.25)
    section.right_margin  = Inches(1.25)

    # ── Title ──────────────────────────────────────────────────────────────
    title_para = doc.add_paragraph()
    _set_paragraph_format(title_para, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)
    run = title_para.add_run(_normalize_quotes(title))
    _set_font(run, FONT_TITLE, SIZE_2, bold=False)

    # ── Body paragraphs ────────────────────────────────────────────────────
    for item in paragraphs_data:
        kind = item.get('type', 'body')
        text = _normalize_quotes(item.get('text', ''))

        if kind == 'h1':
            p = doc.add_paragraph()
            _set_paragraph_format(p, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)
            run = p.add_run(text)
            _set_font(run, FONT_H1, SIZE_3, bold=False)

        elif kind == 'h2':
            p = doc.add_paragraph()
            _set_paragraph_format(p, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=False)
            run = p.add_run(text)
            _set_font(run, FONT_H2, SIZE_3, bold=False)

        elif kind == 'h3_inline':
            # 三级标题：前缀加粗，其余正文字体
            p = doc.add_paragraph()
            _set_paragraph_format(p, first_line_indent=True)
            prefix = item.get('prefix', '')
            rest   = item.get('rest', text)
            if prefix:
                run_prefix = p.add_run(prefix)
                _set_font(run_prefix, FONT_H3_BODY, SIZE_3, bold=True)
            run_rest = p.add_run(rest)
            _set_font(run_rest, FONT_H3_BODY, SIZE_3, bold=False)

        elif kind == 'body':
            p = doc.add_paragraph()
            _set_paragraph_format(p, first_line_indent=True)
            run = p.add_run(text)
            _set_font(run, FONT_BODY, SIZE_3, bold=False)

        elif kind == 'author':
            for line in text.split('\n'):
                if line.strip():
                    p = doc.add_paragraph()
                    _set_paragraph_format(p, align=WD_ALIGN_PARAGRAPH.CENTER,
                                          first_line_indent=False)
                    run = p.add_run(line.strip())
                    _set_font(run, FONT_BODY, SIZE_3, bold=False)

    # ── Page number ────────────────────────────────────────────────────────
    _add_page_number(section)

    return doc


# ── Markdown Parser ────────────────────────────────────────────────────────────

def parse_markdown(md_text):
    """
    Parse Markdown into (title, paragraphs_data) for build_document().

    Heading map:
      # Title          -> document title
      ## H1            -> h1
      ### H2           -> h2
      **prefix** rest  -> h3_inline (bold prefix, plain rest)
      plain text       -> body
    """
    lines = md_text.splitlines()
    title = ''
    paragraphs = []

    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            continue

        if stripped.startswith('### '):
            paragraphs.append({'type': 'h2', 'text': stripped[4:].strip()})

        elif stripped.startswith('## '):
            paragraphs.append({'type': 'h1', 'text': stripped[3:].strip()})

        elif stripped.startswith('# '):
            title = stripped[2:].strip()

        else:
            # Check for bold prefix pattern: **prefix** rest
            m = re.match(r'^\*\*(.+?)\*\*\s*(.*)', stripped)
            if m:
                paragraphs.append({
                    'type': 'h3_inline',
                    'prefix': m.group(1),
                    'rest': m.group(2),
                    'text': stripped,
                })
            else:
                paragraphs.append({'type': 'body', 'text': stripped})

    return title, paragraphs


def main():
    parser = argparse.ArgumentParser(
        description='公文格式规范生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--from-markdown', metavar='FILE', help='Input Markdown file')
    parser.add_argument('--title',   help='Document title (JSON mode)')
    parser.add_argument('--author',  help='Author / signature block (\\n separated)')
    parser.add_argument('--content', metavar='FILE', help='Content JSON file (JSON mode)')
    parser.add_argument('--output',  required=True, metavar='FILE', help='Output .docx file')
    args = parser.parse_args()

    if args.from_markdown:
        md_path = Path(args.from_markdown)
        if not md_path.exists():
            print(f"错误：Markdown 文件不存在: {md_path}", file=sys.stderr)
            sys.exit(1)
        md_text = md_path.read_text(encoding='utf-8')
        title, paragraphs = parse_markdown(md_text)

        if args.author:
            author_text = args.author.replace('\\n', '\n')
            paragraphs.append({'type': 'author', 'text': author_text})

    elif args.content:
        content_path = Path(args.content)
        data = json.loads(content_path.read_text(encoding='utf-8'))
        title = args.title or data.get('title', '')
        paragraphs = data.get('paragraphs', [])
        if args.author:
            author_text = args.author.replace('\\n', '\n')
            paragraphs.append({'type': 'author', 'text': author_text})
    else:
        print("错误：必须提供 --from-markdown 或 --content 参数", file=sys.stderr)
        sys.exit(1)

    doc = build_document(title, args.author or '', paragraphs)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    print(f"✓ 文档已生成：{out_path}")


if __name__ == '__main__':
    main()
PYEOF

chmod +x "$SKILL_DIR/docx-formatter"

# ── Write install.sh ──────────────────────────────────────────────────────────
cat > "$SKILL_DIR/install.sh" << 'EOF'
#!/bin/bash
pip install python-docx lxml -i https://pypi.tuna.tsinghua.edu.cn/simple
echo "依赖安装完成"
EOF
chmod +x "$SKILL_DIR/install.sh"

# ── Symlink into PATH ─────────────────────────────────────────────────────────
ln -sf "$SKILL_DIR/docx-formatter" /usr/local/bin/docx-formatter

# ── Write example ─────────────────────────────────────────────────────────────
cat > "$SKILL_DIR/examples/example.md" << 'EXEOF'
# 示例公文标题

## 一、第一章节

### （一）第一小节

这是正文内容，说明具体情况。

**1. ** 三级标题示例：相关工作顺利推进。
EXEOF

echo "Setup complete. docx-formatter is ready."