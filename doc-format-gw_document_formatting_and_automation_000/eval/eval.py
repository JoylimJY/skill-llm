#!/usr/bin/env python3
"""
Evaluation script for the doc-format-gw task.
Checks that the output .docx file:
1. Exists somewhere in the workspace
2. Has correct page margins
3. Has correct main title formatting (方正小标宋简体, 22pt, centered)
4. Has correct heading1 formatting (黑体, 14pt)
5. Has correct heading2 formatting (楷体_GB2312, 14pt)
6. Has correct heading3 formatting (仿宋_GB2312, 14pt, BOLD)
7. Has correct heading4 formatting (仿宋_GB2312, 14pt, NOT bold)
8. Has correct body text formatting (仿宋_GB2312, 14pt)
9. Has correct table cell font (仿宋_GB2312, 10.5pt)
10. Has page number in footer
"""

import sys
import json
import re
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
except ImportError:
    print(json.dumps({
        "passed": False,
        "score": 0.0,
        "checks": [{"name": "import_check", "passed": False, "detail": "python-docx not installed"}]
    }))
    sys.exit(0)

def get_workspace(argv):
    if len(argv) > 1:
        return Path(argv[1])
    return Path("/workspace")

def emu_to_cm(emu):
    """Convert EMU to cm"""
    return emu / 914400 * 100 / 10  # emu -> inches -> cm? 
    # 1 inch = 914400 EMU, 1 inch = 2.54 cm
    # Actually: emu / 914400 * 2.54

def emu_to_cm_correct(emu):
    return emu / 914400 * 2.54

def pt_to_emu(pt):
    return pt * 12700

def check_font_name(run, expected_font):
    """Check if run has the expected font (via east asia or direct name)"""
    try:
        rPr = run._r.find(qn('w:rPr'))
        if rPr is not None:
            rFonts = rPr.find(qn('w:rFonts'))
            if rFonts is not None:
                ea = rFonts.get(qn('w:eastAsia'), '')
                ascii_f = rFonts.get(qn('w:ascii'), '')
                hAnsi = rFonts.get(qn('w:hAnsi'), '')
                if expected_font in [ea, ascii_f, hAnsi]:
                    return True
        # Also check via python-docx API
        if run.font.name == expected_font:
            return True
        return False
    except Exception:
        return False

def check_font_size(run, expected_pt, tolerance=0.5):
    """Check font size with tolerance"""
    try:
        size = run.font.size
        if size is None:
            return False
        size_pt = size.pt
        return abs(size_pt - expected_pt) <= tolerance
    except Exception:
        return False

def check_line_spacing(para, expected_pt, tolerance=1.0):
    """Check fixed line spacing"""
    try:
        pPr = para._p.find(qn('w:pPr'))
        if pPr is None:
            return False
        spacing = pPr.find(qn('w:spacing'))
        if spacing is None:
            return False
        line_val = spacing.get(qn('w:line'))
        line_rule = spacing.get(qn('w:lineRule'))
        if line_val is None:
            return False
        line_pt = int(line_val) / 20  # twips to pt
        return abs(line_pt - expected_pt) <= tolerance and (line_rule in ['exact', 'atLeast'] if line_rule else True)
    except Exception:
        return False

def main():
    workspace = get_workspace(sys.argv)
    checks = []

    # ── Find output file ────────────────────────────────────────────────────────
    # Look for any .docx file that is NOT the input draft
    input_name = "政务公开实施意见_草稿.docx"
    output_files = [
        f for f in workspace.rglob("*.docx")
        if f.name != input_name
    ]

    if not output_files:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": f"No output .docx file found in workspace (excluding {input_name})"
        })
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    # Use the most recently modified output file
    output_path = sorted(output_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found output file: {output_path}"
    })

    try:
        doc = Document(str(output_path))
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Cannot open output docx: {e}"
        })
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    checks.append({"name": "output_file_readable", "passed": True, "detail": "File opened successfully"})

    # ── Check 1: Page Margins ────────────────────────────────────────────────────
    try:
        section = doc.sections[0]
        top_cm = emu_to_cm_correct(section.top_margin)
        bottom_cm = emu_to_cm_correct(section.bottom_margin)
        left_cm = emu_to_cm_correct(section.left_margin)
        right_cm = emu_to_cm_correct(section.right_margin)

        tol = 0.2
        top_ok = abs(top_cm - 3.7) <= tol
        bottom_ok = abs(bottom_cm - 3.5) <= tol
        left_ok = abs(left_cm - 2.8) <= tol
        right_ok = abs(right_cm - 2.6) <= tol

        margins_ok = top_ok and bottom_ok and left_ok and right_ok
        checks.append({
            "name": "page_margins",
            "passed": margins_ok,
            "detail": (
                f"top={top_cm:.2f}cm (need 3.7), bottom={bottom_cm:.2f}cm (need 3.5), "
                f"left={left_cm:.2f}cm (need 2.8), right={right_cm:.2f}cm (need 2.6)"
            )
        })
    except Exception as e:
        checks.append({"name": "page_margins", "passed": False, "detail": f"Error: {e}"})

    # ── Collect non-empty paragraphs ────────────────────────────────────────────
    paragraphs = [p for p in doc.paragraphs if p.text.strip()]

    # ── Check 2: Main Title (first non-empty paragraph) ─────────────────────────
    try:
        main_title_para = paragraphs[0] if paragraphs else None
        if main_title_para is None:
            raise ValueError("No paragraphs found")

        runs = main_title_para.runs
        if not runs:
            raise ValueError("Main title paragraph has no runs")

        font_ok = any(check_font_name(r, '方正小标宋简体') for r in runs)
        size_ok = any(check_font_size(r, 22.0) for r in runs)
        align_ok = main_title_para.alignment == WD_ALIGN_PARAGRAPH.CENTER

        title_ok = font_ok and size_ok and align_ok
        checks.append({
            "name": "main_title_format",
            "passed": title_ok,
            "detail": (
                f"Text='{main_title_para.text[:20]}...', "
                f"font_ok={font_ok}, size_ok={size_ok}, align_ok={align_ok}"
            )
        })
    except Exception as e:
        checks.append({"name": "main_title_format", "passed": False, "detail": f"Error: {e}"})

    # ── Check 3: Heading 1 format (黑体, 14pt) ──────────────────────────────────
    try:
        heading1_pattern = re.compile(r'^[一二三四五六七八九十]+、')
        h1_paras = [p for p in paragraphs if heading1_pattern.match(p.text.strip())]

        if not h1_paras:
            raise ValueError("No heading1 paragraphs found matching pattern")

        h1_checks = []
        for p in h1_paras[:2]:  # Check first 2
            runs = p.runs
            if not runs:
                h1_checks.append(False)
                continue
            font_ok = any(check_font_name(r, '黑体') for r in runs)
            size_ok = any(check_font_size(r, 14.0) for r in runs)
            h1_checks.append(font_ok and size_ok)

        h1_ok = all(h1_checks) and len(h1_checks) > 0
        checks.append({
            "name": "heading1_format",
            "passed": h1_ok,
            "detail": f"Found {len(h1_paras)} heading1 paras, checks={h1_checks}"
        })
    except Exception as e:
        checks.append({"name": "heading1_format", "passed": False, "detail": f"Error: {e}"})

    # ── Check 4: Heading 2 format (楷体_GB2312, 14pt) ───────────────────────────
    try:
        heading2_pattern = re.compile(r'^（[一二三四五六七八九十]+）')
        h2_paras = [p for p in paragraphs if heading2_pattern.match(p.text.strip())]

        if not h2_paras:
            raise ValueError("No heading2 paragraphs found")

        h2_checks = []
        for p in h2_paras[:2]:
            runs = p.runs
            if not runs:
                h2_checks.append(False)
                continue
            font_ok = any(check_font_name(r, '楷体_GB2312') for r in runs)
            size_ok = any(check_font_size(r, 14.0) for r in runs)
            h2_checks.append(font_ok and size_ok)

        h2_ok = all(h2_checks) and len(h2_checks) > 0
        checks.append({
            "name": "heading2_format",
            "passed": h2_ok,
            "detail": f"Found {len(h2_paras)} heading2 paras, checks={h2_checks}"
        })
    except Exception as e:
        checks.append({"name": "heading2_format", "passed": False, "detail": f"Error: {e}"})

    # ── Check 5: Heading 3 format (仿宋_GB2312, 14pt, BOLD) ─────────────────────
    try:
        heading3_pattern = re.compile(r'^\d+\.')
        h3_paras = [p for p in paragraphs if heading3_pattern.match(p.text.strip())]

        if not h3_paras:
            raise ValueError("No heading3 paragraphs found")

        h3_checks = []
        for p in h3_paras[:2]:
            runs = p.runs
            if not runs:
                h3_checks.append(False)
                continue
            font_ok = any(check_font_name(r, '仿宋_GB2312') for r in runs)
            size_ok = any(check_font_size(r, 14.0) for r in runs)
            bold_ok = any(r.font.bold for r in runs)
            h3_checks.append(font_ok and size_ok and bold_ok)

        h3_ok = all(h3_checks) and len(h3_checks) > 0
        checks.append({
            "name": "heading3_format_bold",
            "passed": h3_ok,
            "detail": f"Found {len(h3_paras)} heading3 paras, checks={h3_checks}"
        })
    except Exception as e:
        checks.append({"name": "heading3_format_bold", "passed": False, "detail": f"Error: {e}"})

    # ── Check 6: Heading 4 format (仿宋_GB2312, 14pt, NOT bold) ─────────────────
    try:
        heading4_pattern = re.compile(r'^（\d+）')
        h4_paras = [p for p in paragraphs if heading4_pattern.match(p.text.strip())]

        if not h4_paras:
            raise ValueError("No heading4 paragraphs found")

        h4_checks = []
        for p in h4_paras[:2]:
            runs = p.runs
            if not runs:
                h4_checks.append(False)
                continue
            font_ok = any(check_font_name(r, '仿宋_GB2312') for r in runs)
            size_ok = any(check_font_size(r, 14.0) for r in runs)
            not_bold = not any(r.font.bold for r in runs)
            h4_checks.append(font_ok and size_ok and not_bold)

        h4_ok = all(h4_checks) and len(h4_checks) > 0
        checks.append({
            "name": "heading4_format_not_bold",
            "passed": h4_ok,
            "detail": f"Found {len(h4_paras)} heading4 paras, checks={h4_checks}"
        })
    except Exception as e:
        checks.append({"name": "heading4_format_not_bold", "passed": False, "detail": f"Error: {e}"})

    # ── Check 7: Body text format (仿宋_GB2312, 14pt) ───────────────────────────
    try:
        # Find body paragraphs (not title, not headings)
        heading_patterns = [
            re.compile(r'^[一二三四五六七八九十]+、'),
            re.compile(r'^（[一二三四五六七八九十]+）'),
            re.compile(r'^\d+\.'),
            re.compile(r'^（\d+）'),
        ]
        body_paras = []
        for i, p in enumerate(paragraphs):
            if i == 0:
                continue  # skip main title
            text = p.text.strip()
            is_heading = any(pat.match(text) for pat in heading_patterns)
            if not is_heading and len(text) > 10:
                body_paras.append(p)

        if not body_paras:
            raise ValueError("No body paragraphs found")

        body_checks = []
        for p in body_paras[:3]:
            runs = p.runs
            if not runs:
                continue
            font_ok = any(check_font_name(r, '仿宋_GB2312') for r in runs)
            size_ok = any(check_font_size(r, 14.0) for r in runs)
            body_checks.append(font_ok and size_ok)

        body_ok = sum(body_checks) >= max(1, len(body_checks) * 0.6)
        checks.append({
            "name": "body_text_format",
            "passed": body_ok,
            "detail": f"Checked {len(body_checks)} body paras, pass_count={sum(body_checks)}"
        })
    except Exception as e:
        checks.append({"name": "body_text_format", "passed": False, "detail": f"Error: {e}"})

    # ── Check 8: Body line spacing (28pt fixed) ──────────────────────────────────
    try:
        spacing_checks = []
        for p in paragraphs[1:6]:  # Check a sample of non-title paragraphs
            spacing_checks.append(check_line_spacing(p, 28.0))

        spacing_ok = sum(spacing_checks) >= max(1, len(spacing_checks) * 0.6)
        checks.append({
            "name": "line_spacing_28pt",
            "passed": spacing_ok,
            "detail": f"Spacing checks: {spacing_checks}"
        })
    except Exception as e:
        checks.append({"name": "line_spacing_28pt", "passed": False, "detail": f"Error: {e}"})

    # ── Check 9: Table cell font (仿宋_GB2312, 10.5pt) ──────────────────────────
    try:
        if not doc.tables:
            raise ValueError("No tables found in document")

        table = doc.tables[0]
        table_font_checks = []
        for row in table.rows[1:]:  # Skip header row, check data rows
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        font_ok = check_font_name(run, '仿宋_GB2312')
                        size_ok = check_font_size(run, 10.5, tolerance=0.6)
                        table_font_checks.append(font_ok and size_ok)

        if not table_font_checks:
            raise ValueError("No runs found in table data cells")

        table_ok = sum(table_font_checks) >= len(table_font_checks) * 0.5
        checks.append({
            "name": "table_font_format",
            "passed": table_ok,
            "detail": f"Table cell checks: {sum(table_font_checks)}/{len(table_font_checks)} passed"
        })
    except Exception as e:
        checks.append({"name": "table_font_format", "passed": False, "detail": f"Error: {e}"})

    # ── Check 10: Footer has page number field ───────────────────────────────────
    try:
        footer_has_page = False
        for section in doc.sections:
            footer = section.footer
            footer_xml = footer._element.xml
            if 'PAGE' in footer_xml or 'fldChar' in footer_xml or 'instrText' in footer_xml:
                footer_has_page = True
                break

        checks.append({
            "name": "footer_page_number",
            "passed": footer_has_page,
            "detail": f"Footer page number field found: {footer_has_page}"
        })
    except Exception as e:
        checks.append({"name": "footer_page_number", "passed": False, "detail": f"Error: {e}"})

    # ── Compute score ────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total if total > 0 else 0.0
    passed = score >= 0.75  # Must pass at least 75% of checks

    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()