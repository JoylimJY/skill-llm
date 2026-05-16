#!/usr/bin/env python3
"""
Evaluation script for md2word-cn task.
Checks that the agent correctly converted weekly_report_42.md → weekly_report_42.docx
with the proper proprietary formatting constraints.
"""

import sys
import json
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
except ImportError:
    print(json.dumps({
        "passed": False, "score": 0.0,
        "checks": [{"name": "dependency_check", "passed": False,
                    "detail": "python-docx not installed in eval environment"}]
    }))
    sys.exit(0)


def get_run_font_name(run):
    """Extract east-asia or latin font name from a run."""
    try:
        rPr = run._element.rPr
        if rPr is not None:
            rFonts = rPr.find(qn('w:rFonts'))
            if rFonts is not None:
                ea = rFonts.get(qn('w:eastAsia'))
                if ea:
                    return ea
        if run.font.name:
            return run.font.name
    except Exception:
        pass
    return None


def pt_value(size_obj):
    """Convert docx Pt/Emu size to float pt value."""
    if size_obj is None:
        return None
    try:
        return size_obj.pt
    except Exception:
        try:
            return size_obj / 12700.0
        except Exception:
            return None


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []

    # ── 1. Find the output file ──────────────────────────────────────────────
    candidates = list(workspace.rglob("weekly_report_42.docx"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named 'weekly_report_42.docx'" if file_found
                  else "No file named 'weekly_report_42.docx' found anywhere in workspace"
    })
    if not file_found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    docx_path = candidates[0]

    try:
        doc = Document(str(docx_path))
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False,
                       "detail": f"Could not open docx: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "file_readable", "passed": True,
                   "detail": f"Opened {docx_path.name} successfully"})

    paragraphs = doc.paragraphs

    # ── 2. Non-empty document ────────────────────────────────────────────────
    non_empty = [p for p in paragraphs if p.text.strip()]
    enough_content = len(non_empty) >= 15
    checks.append({
        "name": "sufficient_content",
        "passed": enough_content,
        "detail": f"Found {len(non_empty)} non-empty paragraphs (need ≥15)"
    })

    # ── 3. H1 heading: centered, ~22pt, bold, 仿宋 ──────────────────────────
    h1_check_passed = False
    h1_detail = "H1 heading paragraph not found"
    for p in paragraphs:
        text = p.text.strip()
        if "第42周工作周报" in text or "某市行政服务中心" in text:
            # Check alignment
            aligned_center = (p.alignment == WD_ALIGN_PARAGRAPH.CENTER)
            # Check runs
            size_ok = False
            bold_ok = False
            font_ok = False
            for run in p.runs:
                sz = pt_value(run.font.size)
                if sz and abs(sz - 22.0) < 1.0:
                    size_ok = True
                if run.font.bold:
                    bold_ok = True
                fname = get_run_font_name(run)
                if fname and "仿宋" in fname:
                    font_ok = True
            h1_check_passed = aligned_center and size_ok and bold_ok and font_ok
            h1_detail = (
                f"H1 '{text[:30]}': centered={aligned_center}, "
                f"22pt={size_ok}, bold={bold_ok}, 仿宋={font_ok}"
            )
            break
    checks.append({"name": "h1_format_centered_22pt_bold_fangsong",
                   "passed": h1_check_passed, "detail": h1_detail})

    # ── 4. H2 heading: ~16pt, bold, 仿宋, NOT centered ──────────────────────
    h2_check_passed = False
    h2_detail = "H2 heading paragraph not found"
    for p in paragraphs:
        text = p.text.strip()
        if text.startswith("一、") or "本周工作概况" in text:
            size_ok = False
            bold_ok = False
            font_ok = False
            not_centered = (p.alignment != WD_ALIGN_PARAGRAPH.CENTER)
            for run in p.runs:
                sz = pt_value(run.font.size)
                if sz and abs(sz - 16.0) < 1.0:
                    size_ok = True
                if run.font.bold:
                    bold_ok = True
                fname = get_run_font_name(run)
                if fname and "仿宋" in fname:
                    font_ok = True
            h2_check_passed = size_ok and bold_ok and font_ok and not_centered
            h2_detail = (
                f"H2 '{text[:30]}': 16pt={size_ok}, bold={bold_ok}, "
                f"仿宋={font_ok}, not_centered={not_centered}"
            )
            break
    checks.append({"name": "h2_format_16pt_bold_fangsong",
                   "passed": h2_check_passed, "detail": h2_detail})

    # ── 5. H3 heading: ~14pt, bold, 仿宋 ────────────────────────────────────
    h3_check_passed = False
    h3_detail = "H3 heading paragraph not found"
    for p in paragraphs:
        text = p.text.strip()
        if "窗口服务情况" in text or "1.1" in text:
            size_ok = False
            bold_ok = False
            font_ok = False
            for run in p.runs:
                sz = pt_value(run.font.size)
                if sz and abs(sz - 14.0) < 1.0:
                    size_ok = True
                if run.font.bold:
                    bold_ok = True
                fname = get_run_font_name(run)
                if fname and "仿宋" in fname:
                    font_ok = True
            h3_check_passed = size_ok and bold_ok and font_ok
            h3_detail = (
                f"H3 '{text[:30]}': 14pt={size_ok}, bold={bold_ok}, 仿宋={font_ok}"
            )
            break
    checks.append({"name": "h3_format_14pt_bold_fangsong",
                   "passed": h3_check_passed, "detail": h3_detail})

    # ── 6. H4 heading: ~12pt, bold, 仿宋 ────────────────────────────────────
    h4_check_passed = False
    h4_detail = "H4 heading paragraph not found"
    for p in paragraphs:
        text = p.text.strip()
        if "高频事项统计" in text or "1.1.1" in text:
            size_ok = False
            bold_ok = False
            font_ok = False
            for run in p.runs:
                sz = pt_value(run.font.size)
                if sz and abs(sz - 12.0) < 1.5:
                    size_ok = True
                if run.font.bold:
                    bold_ok = True
                fname = get_run_font_name(run)
                if fname and "仿宋" in fname:
                    font_ok = True
            h4_check_passed = size_ok and bold_ok and font_ok
            h4_detail = (
                f"H4 '{text[:30]}': 12pt={size_ok}, bold={bold_ok}, 仿宋={font_ok}"
            )
            break
    checks.append({"name": "h4_format_12pt_bold_fangsong",
                   "passed": h4_check_passed, "detail": h4_detail})

    # ── 7. Ordered list: manual numbering (text starts with digit+dot) ───────
    ol_check_passed = False
    ol_detail = "No manually-numbered list item found"
    ol_items_found = []
    for p in paragraphs:
        text = p.text.strip()
        # Manual numbering: text literally starts with "1." "2." etc.
        if re.match(r'^\d+[.．]', text):
            ol_items_found.append(text[:40])
            # Must NOT use Word's list style (numId in pPr means auto-numbering)
            pPr = p._element.find(qn('w:pPr'))
            has_numPr = False
            if pPr is not None:
                numPr = pPr.find(qn('w:numPr'))
                if numPr is not None:
                    has_numPr = True
            if not has_numPr:
                ol_check_passed = True
                ol_detail = f"Found manual OL item '{text[:40]}' without Word auto-numbering"
                break
    if ol_items_found and not ol_check_passed:
        ol_detail = (f"Found {len(ol_items_found)} OL-like items but they use "
                     f"Word's auto-numbering (numPr present) instead of manual text")
    elif not ol_items_found:
        ol_detail = "No paragraph starting with digit+dot found"

    import re
    checks.append({"name": "ordered_list_manual_numbering",
                   "passed": ol_check_passed, "detail": ol_detail})

    # ── 8. Body text font is 仿宋 ─────────────────────────────────────────────
    body_font_ok = False
    body_font_detail = "No body-text paragraph with 仿宋 font found"
    fangsong_count = 0
    total_run_count = 0
    for p in paragraphs:
        text = p.text.strip()
        if not text or len(text) < 5:
            continue
        # Skip heading-like paragraphs (bold-only short ones)
        is_likely_heading = all(r.font.bold for r in p.runs if r.text.strip())
        if is_likely_heading and len(text) < 30:
            continue
        for run in p.runs:
            if not run.text.strip():
                continue
            total_run_count += 1
            fname = get_run_font_name(run)
            if fname and "仿宋" in fname:
                fangsong_count += 1
    if total_run_count > 0:
        ratio = fangsong_count / total_run_count
        body_font_ok = ratio >= 0.5
        body_font_detail = (f"仿宋 font found in {fangsong_count}/{total_run_count} "
                            f"runs ({ratio*100:.1f}%); threshold=50%")
    checks.append({"name": "body_font_fangsong",
                   "passed": body_font_ok, "detail": body_font_detail})

    # ── 9. Code block present ────────────────────────────────────────────────
    code_block_found = False
    code_block_detail = "No code block paragraph found"
    for p in paragraphs:
        text = p.text.strip()
        if "模块一" in text or "模块二" in text or "OCR" in text or "身份核验" in text:
            code_block_found = True
            code_block_detail = f"Code block content found: '{text[:50]}'"
            break
    checks.append({"name": "code_block_content_present",
                   "passed": code_block_found, "detail": code_block_detail})

    # ── 10. Inline bold text preserved ──────────────────────────────────────
    bold_inline_found = False
    bold_inline_detail = "No bold inline run found in body text"
    for p in paragraphs:
        text = p.text.strip()
        if not text:
            continue
        for run in p.runs:
            if run.font.bold and run.text.strip() and len(run.text.strip()) < 20:
                # Make sure it's not a heading paragraph
                if len(text) > 15:
                    bold_inline_found = True
                    bold_inline_detail = f"Bold inline run found: '{run.text}' in '{text[:40]}'"
                    break
        if bold_inline_found:
            break
    checks.append({"name": "inline_bold_preserved",
                   "passed": bold_inline_found, "detail": bold_inline_detail})

    # ── Final scoring ────────────────────────────────────────────────────────
    critical = [
        "output_file_exists", "file_readable",
        "h1_format_centered_22pt_bold_fangsong",
        "h2_format_16pt_bold_fangsong",
        "ordered_list_manual_numbering",
        "body_font_fangsong",
    ]
    all_checks = {c["name"]: c["passed"] for c in checks}
    critical_passed = all(all_checks.get(n, False) for n in critical)
    total_passed = sum(1 for c in checks if c["passed"])
    score = round(total_passed / len(checks), 3)
    overall_passed = critical_passed and score >= 0.7

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))


import re
if __name__ == "__main__":
    main()