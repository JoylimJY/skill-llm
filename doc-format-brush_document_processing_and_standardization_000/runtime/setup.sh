#!/bin/bash
set -e

SKILLS_DIR="/workspace/skills/doc-format-brush/scripts"
mkdir -p "$SKILLS_DIR"

# ============================================================
# Write extract_format.py
# ============================================================
cat > "$SKILLS_DIR/extract_format.py" << 'PYEOF'
#!/usr/bin/env python3
"""Extract formatting information from a Word (.docx) template file."""
import argparse
import json
import sys
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn

def extract_format(docx_path: str) -> dict:
    doc = Document(docx_path)
    section = doc.sections[0]
    
    page_setup = {
        "page_width_cm": round(section.page_width.cm, 2),
        "page_height_cm": round(section.page_height.cm, 2),
        "top_margin_cm": round(section.top_margin.cm, 2),
        "bottom_margin_cm": round(section.bottom_margin.cm, 2),
        "left_margin_cm": round(section.left_margin.cm, 2),
        "right_margin_cm": round(section.right_margin.cm, 2),
    }
    
    paragraph_styles = {}
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        
        # Determine paragraph type
        para_type = classify_paragraph_type(para, doc)
        
        if para_type in paragraph_styles:
            continue  # Already captured this type
        
        style_info = extract_paragraph_style(para)
        paragraph_styles[para_type] = style_info
    
    return {
        "page_setup": page_setup,
        "paragraph_styles": paragraph_styles,
        "source_file": str(docx_path),
    }

def classify_paragraph_type(para, doc):
    """Classify paragraph into title/wenhao/heading1/heading2/body."""
    text = para.text.strip()
    
    all_paras = [p for p in doc.paragraphs if p.text.strip()]
    
    if not all_paras:
        return "body"
    
    if para == all_paras[0]:
        return "title"
    
    if len(all_paras) > 1 and para == all_paras[1]:
        # Check for document number pattern
        import re
        if re.search(r'[〔（\[].{0,6}[〕）\]]', text):
            return "wenhao"
    
    # Check for heading patterns
    import re
    if re.match(r'^[一二三四五六七八九十]+[、．.]', text):
        return "heading1"
    if re.match(r'^（[一二三四五六七八九十]+）', text):
        return "heading2"
    
    return "body"

def extract_paragraph_style(para) -> dict:
    pf = para.paragraph_format
    
    # Extract alignment
    alignment = None
    if pf.alignment is not None:
        alignment = str(pf.alignment)
    
    # Extract spacing
    space_before_pt = float(pf.space_before.pt) if pf.space_before else 0.0
    space_after_pt = float(pf.space_after.pt) if pf.space_after else 0.0
    
    # Extract line spacing
    line_spacing_pt = None
    if pf.line_spacing is not None:
        try:
            line_spacing_pt = float(pf.line_spacing.pt)
        except:
            line_spacing_pt = float(pf.line_spacing) if pf.line_spacing else None
    
    # Extract first line indent (character-based from XML)
    first_line_chars = 0
    pPr = para._p.find(qn('w:pPr'))
    if pPr is not None:
        ind = pPr.find(qn('w:ind'))
        if ind is not None:
            flc = ind.get(qn('w:firstLineChars'))
            if flc:
                first_line_chars = int(flc) // 100
    
    # Extract font info from first run
    font_name = None
    font_size_pt = None
    bold = False
    
    for run in para.runs:
        if run.text.strip():
            font_name = run.font.name
            # Try to get east asia font
            rPr = run._r.find(qn('w:rPr'))
            if rPr is not None:
                rFonts = rPr.find(qn('w:rFonts'))
                if rFonts is not None:
                    ea = rFonts.get(qn('w:eastAsia'))
                    if ea:
                        font_name = ea
            font_size_pt = float(run.font.size.pt) if run.font.size else None
            bold = bool(run.font.bold)
            break
    
    return {
        "font_name": font_name,
        "font_size_pt": font_size_pt,
        "bold": bold,
        "alignment": alignment,
        "first_line_chars": first_line_chars,
        "space_before_pt": space_before_pt,
        "space_after_pt": space_after_pt,
        "line_spacing_pt": line_spacing_pt,
    }

def main():
    parser = argparse.ArgumentParser(description="Extract format from a Word template")
    parser.add_argument("template", help="Path to template .docx file")
    parser.add_argument("--output", "-o", required=True, help="Output JSON file path")
    args = parser.parse_args()
    
    template_path = Path(args.template)
    if not template_path.exists():
        print(f"Error: Template file not found: {template_path}", file=sys.stderr)
        sys.exit(1)
    
    if not str(template_path).endswith(".docx"):
        print(f"Error: Template must be a .docx file", file=sys.stderr)
        sys.exit(1)
    
    format_data = extract_format(str(template_path))
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(format_data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"Format extracted to: {output_path}")
    print(f"Found styles: {list(format_data['paragraph_styles'].keys())}")

if __name__ == "__main__":
    main()
PYEOF

# ============================================================
# Write format_bridge.py
# ============================================================
cat > "$SKILLS_DIR/format_bridge.py" << 'PYEOF'
#!/usr/bin/env python3
"""Core library for reading/writing multi-format documents."""
import re
from pathlib import Path
from typing import List, Tuple


PARAGRAPH_TYPE_TITLE = "title"
PARAGRAPH_TYPE_WENHAO = "wenhao"
PARAGRAPH_TYPE_HEADING1 = "heading1"
PARAGRAPH_TYPE_HEADING2 = "heading2"
PARAGRAPH_TYPE_BODY = "body"
PARAGRAPH_TYPE_LIST = "list"


def read_document(file_path: str) -> List[Tuple[str, str]]:
    """Read a document and return list of (paragraph_type, text) tuples."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == ".docx":
        return _read_docx(file_path)
    elif suffix == ".md":
        return _read_markdown(file_path)
    elif suffix == ".txt":
        return _read_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def _read_docx(file_path: str) -> List[Tuple[str, str]]:
    from docx import Document
    from docx.oxml.ns import qn
    import re
    
    doc = Document(file_path)
    paragraphs = [p for p in doc.paragraphs if p.text.strip()]
    result = []
    
    for i, para in enumerate(paragraphs):
        text = para.text.strip()
        
        if i == 0:
            para_type = PARAGRAPH_TYPE_TITLE
        elif i == 1 and re.search(r'[〔（\[].{0,6}[〕）\]]', text):
            para_type = PARAGRAPH_TYPE_WENHAO
        elif re.match(r'^[一二三四五六七八九十]+[、．.]', text):
            para_type = PARAGRAPH_TYPE_HEADING1
        elif re.match(r'^（[一二三四五六七八九十]+）', text):
            para_type = PARAGRAPH_TYPE_HEADING2
        else:
            para_type = PARAGRAPH_TYPE_BODY
        
        result.append((para_type, text))
    
    return result


def _read_markdown(file_path: str) -> List[Tuple[str, str]]:
    content = Path(file_path).read_text(encoding="utf-8")
    lines = content.split("\n")
    result = []
    title_found = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        if stripped.startswith("# ") and not stripped.startswith("## "):
            text = stripped[2:].strip()
            para_type = PARAGRAPH_TYPE_TITLE
            title_found = True
        elif stripped.startswith("## ") and not stripped.startswith("### "):
            text = stripped[3:].strip()
            # Check if it's actually a heading1 pattern in the text
            if re.match(r'^[一二三四五六七八九十]+[、．.]', text):
                para_type = PARAGRAPH_TYPE_HEADING1
            else:
                para_type = PARAGRAPH_TYPE_HEADING1
        elif stripped.startswith("### "):
            text = stripped[4:].strip()
            # Strip inner markdown heading markers if nested
            if re.match(r'^（[一二三四五六七八九十]+）', text):
                para_type = PARAGRAPH_TYPE_HEADING2
            else:
                para_type = PARAGRAPH_TYPE_HEADING2
        elif stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:].strip()
            para_type = PARAGRAPH_TYPE_LIST
        else:
            text = stripped
            para_type = PARAGRAPH_TYPE_BODY
        
        result.append((para_type, text))
    
    return result


def _read_txt(file_path: str) -> List[Tuple[str, str]]:
    import re
    content = Path(file_path).read_text(encoding="utf-8")
    lines = content.split("\n")
    result = []
    first_non_empty = True
    second_check_done = False
    
    non_empty_lines = [l.strip() for l in lines if l.strip()]
    
    for i, text in enumerate(non_empty_lines):
        if i == 0:
            para_type = PARAGRAPH_TYPE_TITLE
        elif i == 1 and re.search(r'[〔（\[].{0,6}[〕）\]]', text):
            para_type = PARAGRAPH_TYPE_WENHAO
        elif re.match(r'^[一二三四五六七八九十]+[、．.]', text):
            para_type = PARAGRAPH_TYPE_HEADING1
        elif re.match(r'^（[一二三四五六七八九十]+）', text):
            para_type = PARAGRAPH_TYPE_HEADING2
        else:
            para_type = PARAGRAPH_TYPE_BODY
        
        result.append((para_type, text))
    
    return result


def write_document(paragraphs: List[Tuple[str, str]], file_path: str, format_data: dict):
    """Write paragraphs to a file, applying format_data styles."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if suffix == ".docx":
        _write_docx(paragraphs, file_path, format_data)
    elif suffix == ".md":
        _write_markdown(paragraphs, file_path, format_data)
    elif suffix == ".txt":
        _write_txt(paragraphs, file_path)
    else:
        raise ValueError(f"Unsupported output format: {suffix}")


def _write_docx(paragraphs: List[Tuple[str, str]], file_path: str, format_data: dict):
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    
    doc = Document()
    
    # Apply page setup
    page_setup = format_data.get("page_setup", {})
    section = doc.sections[0]
    if page_setup:
        if "top_margin_cm" in page_setup:
            section.top_margin = Cm(page_setup["top_margin_cm"])
        if "bottom_margin_cm" in page_setup:
            section.bottom_margin = Cm(page_setup["bottom_margin_cm"])
        if "left_margin_cm" in page_setup:
            section.left_margin = Cm(page_setup["left_margin_cm"])
        if "right_margin_cm" in page_setup:
            section.right_margin = Cm(page_setup["right_margin_cm"])
        if "page_width_cm" in page_setup:
            section.page_width = Cm(page_setup["page_width_cm"])
        if "page_height_cm" in page_setup:
            section.page_height = Cm(page_setup["page_height_cm"])
    
    styles_map = format_data.get("paragraph_styles", {})
    
    ALIGN_MAP = {
        "CENTER": WD_ALIGN_PARAGRAPH.CENTER,
        "WD_ALIGN_PARAGRAPH.CENTER": WD_ALIGN_PARAGRAPH.CENTER,
        "LEFT": WD_ALIGN_PARAGRAPH.LEFT,
        "WD_ALIGN_PARAGRAPH.LEFT": WD_ALIGN_PARAGRAPH.LEFT,
        "JUSTIFY": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "WD_ALIGN_PARAGRAPH.JUSTIFY": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "RIGHT": WD_ALIGN_PARAGRAPH.RIGHT,
        "WD_ALIGN_PARAGRAPH.RIGHT": WD_ALIGN_PARAGRAPH.RIGHT,
    }
    
    for para_type, text in paragraphs:
        para = doc.add_paragraph()
        run = para.add_run(text)
        
        # Map list type to body style
        style_key = para_type
        if style_key == PARAGRAPH_TYPE_LIST:
            style_key = PARAGRAPH_TYPE_BODY
        
        style = styles_map.get(style_key, styles_map.get(PARAGRAPH_TYPE_BODY, {}))
        
        pf = para.paragraph_format
        
        # Font
        if style.get("font_name"):
            run.font.name = style["font_name"]
            rPr = run._r.get_or_add_rPr()
            rFonts = rPr.find(qn('w:rFonts'))
            if rFonts is None:
                rFonts = OxmlElement('w:rFonts')
                rPr.insert(0, rFonts)
            rFonts.set(qn('w:eastAsia'), style["font_name"])
        
        if style.get("font_size_pt"):
            run.font.size = Pt(style["font_size_pt"])
        
        run.font.bold = style.get("bold", False)
        
        # Alignment
        align_str = style.get("alignment", "LEFT")
        if align_str:
            # Extract just the name part
            align_key = align_str.split(".")[-1] if "." in align_str else align_str
            pf.alignment = ALIGN_MAP.get(align_key, WD_ALIGN_PARAGRAPH.LEFT)
        
        # Spacing
        pf.space_before = Pt(style.get("space_before_pt", 0))
        pf.space_after = Pt(style.get("space_after_pt", 0))
        
        # Line spacing
        if style.get("line_spacing_pt"):
            pf.line_spacing = Pt(style["line_spacing_pt"])
        
        # First line indent (character-based)
        flc = style.get("first_line_chars", 0)
        if flc and flc > 0:
            pPr = para._p.get_or_add_pPr()
            ind = pPr.find(qn('w:ind'))
            if ind is None:
                ind = OxmlElement('w:ind')
                pPr.append(ind)
            ind.set(qn('w:firstLineChars'), str(flc * 100))
            ind.set(qn('w:firstLine'), str(flc * 160))
    
    doc.save(file_path)


def _write_markdown(paragraphs: List[Tuple[str, str]], file_path: str, format_data: dict):
    lines = []
    for para_type, text in paragraphs:
        if para_type == PARAGRAPH_TYPE_TITLE:
            lines.append(f"# {text}")
        elif para_type == PARAGRAPH_TYPE_WENHAO:
            lines.append(f"\n> {text}")
        elif para_type == PARAGRAPH_TYPE_HEADING1:
            lines.append(f"\n## {text}")
        elif para_type == PARAGRAPH_TYPE_HEADING2:
            lines.append(f"\n### {text}")
        elif para_type == PARAGRAPH_TYPE_LIST:
            lines.append(f"- {text}")
        else:
            lines.append(f"\n{text}")
    
    Path(file_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_txt(paragraphs: List[Tuple[str, str]], file_path: str):
    lines = [text for _, text in paragraphs]
    Path(file_path).write_text("\n\n".join(lines) + "\n", encoding="utf-8")
PYEOF

# ============================================================
# Write apply_multi_format.py
# ============================================================
cat > "$SKILLS_DIR/apply_multi_format.py" << 'PYEOF'
#!/usr/bin/env python3
"""
Multi-format document format brush tool.

Usage:
  # Official format (GB/T 9704-2012):
  python apply_multi_format.py <input> --official --output <output>

  # Template-based:
  python apply_multi_format.py <input> <template.docx> --output <output>

  # JSON format file:
  python apply_multi_format.py <input> --format-json <format.json> --output <output>
"""
import argparse
import json
import sys
from pathlib import Path

# Add parent dir to path to find format_bridge
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from format_bridge import read_document, write_document

# GB/T 9704-2012 Official Document Format
OFFICIAL_FORMAT = {
    "page_setup": {
        "page_width_cm": 21.0,
        "page_height_cm": 29.7,
        "top_margin_cm": 3.7,
        "bottom_margin_cm": 3.5,
        "left_margin_cm": 2.8,
        "right_margin_cm": 2.6,
    },
    "paragraph_styles": {
        "title": {
            "font_name": "方正小标宋体",
            "font_size_pt": 22.0,
            "bold": False,
            "alignment": "CENTER",
            "first_line_chars": 0,
            "space_before_pt": 0.0,
            "space_after_pt": 0.0,
            "line_spacing_pt": 33.0,
        },
        "wenhao": {
            "font_name": "仿宋_GB2312",
            "font_size_pt": 16.0,
            "bold": False,
            "alignment": "CENTER",
            "first_line_chars": 0,
            "space_before_pt": 0.0,
            "space_after_pt": 0.0,
            "line_spacing_pt": 24.0,
        },
        "heading1": {
            "font_name": "黑体",
            "font_size_pt": 16.0,
            "bold": False,
            "alignment": "LEFT",
            "first_line_chars": 0,
            "space_before_pt": 0.0,
            "space_after_pt": 0.0,
            "line_spacing_pt": 24.0,
        },
        "heading2": {
            "font_name": "楷体_GB2312",
            "font_size_pt": 16.0,
            "bold": False,
            "alignment": "LEFT",
            "first_line_chars": 0,
            "space_before_pt": 0.0,
            "space_after_pt": 0.0,
            "line_spacing_pt": 24.0,
        },
        "body": {
            "font_name": "仿宋_GB2312",
            "font_size_pt": 16.0,
            "bold": False,
            "alignment": "JUSTIFY",
            "first_line_chars": 2,
            "space_before_pt": 0.0,
            "space_after_pt": 0.0,
            "line_spacing_pt": 24.0,
        },
        "list": {
            "font_name": "仿宋_GB2312",
            "font_size_pt": 16.0,
            "bold": False,
            "alignment": "JUSTIFY",
            "first_line_chars": 2,
            "space_before_pt": 0.0,
            "space_after_pt": 0.0,
            "line_spacing_pt": 24.0,
        },
    }
}


def main():
    parser = argparse.ArgumentParser(description="Apply document formatting")
    parser.add_argument("input", help="Input document (docx/md/txt)")
    parser.add_argument("template", nargs="?", default=None, help="Template .docx file (optional)")
    parser.add_argument("--official", action="store_true", help="Use built-in GB/T 9704-2012 format")
    parser.add_argument("--format-json", dest="format_json", default=None, help="Path to format JSON file")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    
    args = parser.parse_args()
    
    # Determine format source
    format_data = None
    
    if args.official:
        format_data = OFFICIAL_FORMAT
        print("Using built-in GB/T 9704-2012 official document format")
    elif args.format_json:
        json_path = Path(args.format_json)
        if not json_path.exists():
            print(f"Error: Format JSON not found: {json_path}", file=sys.stderr)
            sys.exit(1)
        format_data = json.loads(json_path.read_text(encoding="utf-8"))
        print(f"Using format from JSON: {json_path}")
    elif args.template:
        template_path = Path(args.template)
        if not template_path.exists():
            print(f"Error: Template not found: {template_path}", file=sys.stderr)
            sys.exit(1)
        # Import extract_format inline
        from extract_format import extract_format
        format_data = extract_format(str(template_path))
        print(f"Using format extracted from template: {template_path}")
    else:
        print("Error: Must specify one of --official, --format-json, or a template file", file=sys.stderr)
        sys.exit(1)
    
    # Read input document
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Reading input: {input_path}")
    paragraphs = read_document(str(input_path))
    print(f"Detected {len(paragraphs)} paragraphs")
    for ptype, text in paragraphs[:5]:
        print(f"  [{ptype}] {text[:50]}")
    
    # Write output
    output_path = Path(args.output)
    print(f"Writing output: {output_path}")
    write_document(paragraphs, str(output_path), format_data)
    
    print(f"Done! Output saved to: {output_path}")


if __name__ == "__main__":
    main()
PYEOF

# ============================================================
# Write apply_format.py
# ============================================================
cat > "$SKILLS_DIR/apply_format.py" << 'PYEOF'
#!/usr/bin/env python3
"""Apply format JSON to a Word document (Word-only legacy tool)."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from format_bridge import read_document, write_document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input .docx file")
    parser.add_argument("--format-json", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    format_data = json.loads(Path(args.format_json).read_text(encoding="utf-8"))
    paragraphs = read_document(args.input)
    write_document(paragraphs, args.output, format_data)
    print(f"Applied format to {args.output}")


if __name__ == "__main__":
    main()
PYEOF

chmod +x "$SKILLS_DIR/extract_format.py"
chmod +x "$SKILLS_DIR/apply_multi_format.py"
chmod +x "$SKILLS_DIR/apply_format.py"
chmod +x "$SKILLS_DIR/format_bridge.py"

echo "Skills directory setup complete: $SKILLS_DIR"
ls -la "$SKILLS_DIR"