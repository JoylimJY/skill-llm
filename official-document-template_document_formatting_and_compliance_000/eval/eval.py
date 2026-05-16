#!/usr/bin/env python3
"""
Evaluation script for the official-document task.
Checks that the agent produced a valid GB/T 9704-2012 compliant Word document.
"""
import sys
import json
from pathlib import Path

def find_output_docx(workspace):
    """Find the target output file."""
    ws = Path(workspace)
    # The prompt asks for 'water_resource_notice.docx'
    candidates = list(ws.rglob("water_resource_notice.docx"))
    if not candidates:
        # Also accept any .docx that is NOT a placeholder
        candidates = [
            f for f in ws.rglob("*.docx")
            if ".placeholder" not in f.name and "old_versions" not in str(f)
        ]
    return candidates[0] if candidates else None

def mm_to_emu(mm):
    return int(mm * 36000)

def pt_to_emu(pt):
    return int(pt * 12700)

def run_eval(workspace):
    checks = []
    
    # ── Check 1: Output file exists ─────────────────────────────────────────
    try:
        docx_path = find_output_docx(workspace)
        if docx_path is None:
            checks.append({
                "name": "output_file_exists",
                "passed": False,
                "detail": "No .docx output file found in workspace. Expected 'water_resource_notice.docx'."
            })
            return checks, 0.0
        checks.append({
            "name": "output_file_exists",
            "passed": True,
            "detail": f"Found output file: {docx_path}"
        })
    except Exception as e:
        checks.append({"name": "output_file_exists", "passed": False, "detail": str(e)})
        return checks, 0.0

    # ── Load the document ────────────────────────────────────────────────────
    try:
        from docx import Document
        from docx.shared import Mm, Pt
        from docx.oxml.ns import qn
        doc = Document(str(docx_path))
    except Exception as e:
        checks.append({"name": "document_parseable", "passed": False, "detail": f"Failed to parse docx: {e}"})
        return checks, 0.0

    checks.append({"name": "document_parseable", "passed": True, "detail": "Document parsed successfully."})

    # ── Check 2: Page margins (GB/T 9704-2012) ──────────────────────────────
    try:
        section = doc.sections[0]
        top_mm = section.top_margin.mm if section.top_margin else None
        bottom_mm = section.bottom_margin.mm if section.bottom_margin else None
        left_mm = section.left_margin.mm if section.left_margin else None
        right_mm = section.right_margin.mm if section.right_margin else None

        margin_ok = (
            top_mm is not None and abs(top_mm - 37) < 1.5 and
            bottom_mm is not None and abs(bottom_mm - 35) < 1.5 and
            left_mm is not None and abs(left_mm - 28) < 1.5 and
            right_mm is not None and abs(right_mm - 26) < 1.5
        )
        checks.append({
            "name": "page_margins_correct",
            "passed": margin_ok,
            "detail": (
                f"Margins: top={top_mm:.1f}mm (expect 37), bottom={bottom_mm:.1f}mm (expect 35), "
                f"left={left_mm:.1f}mm (expect 28), right={right_mm:.1f}mm (expect 26)"
                if top_mm else "Could not read margins."
            )
        })
    except Exception as e:
        checks.append({"name": "page_margins_correct", "passed": False, "detail": str(e)})

    # ── Check 3: Document has substantial content ────────────────────────────
    try:
        paragraphs = [p for p in doc.paragraphs if p.text.strip()]
        has_content = len(paragraphs) >= 10
        checks.append({
            "name": "document_has_content",
            "passed": has_content,
            "detail": f"Found {len(paragraphs)} non-empty paragraphs (expect >= 10)."
        })
    except Exception as e:
        checks.append({"name": "document_has_content", "passed": False, "detail": str(e)})

    # ── Check 4: Title detected (centered, larger font) ──────────────────────
    try:
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        title_found = False
        for para in doc.paragraphs:
            text = para.text.strip()
            if "关于加强水资源保护和节约用水工作的通知" in text:
                title_found = True
                # Check alignment is center
                align_ok = (para.alignment == WD_ALIGN_PARAGRAPH.CENTER)
                checks.append({
                    "name": "title_found_and_centered",
                    "passed": align_ok,
                    "detail": f"Title found. Alignment: {para.alignment} (expect CENTER=1)."
                })
                break
        if not title_found:
            checks.append({
                "name": "title_found_and_centered",
                "passed": False,
                "detail": "Document title '关于加强水资源保护和节约用水工作的通知' not found in any paragraph."
            })
    except Exception as e:
        checks.append({"name": "title_found_and_centered", "passed": False, "detail": str(e)})

    # ── Check 5: Level-1 heading uses 黑体 font ──────────────────────────────
    try:
        level1_patterns = ["一、总体要求", "二、重点工作任务", "三、保障措施"]
        heiti_found = 0
        heiti_detail = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            matched = any(text.startswith(p) or p in text for p in level1_patterns)
            if matched and para.runs:
                for run in para.runs:
                    font_name = run.font.name
                    # Also check east asia font
                    rPr = run._r.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
                    east_asia_font = None
                    if rPr is not None:
                        rFonts = rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts')
                        if rFonts is not None:
                            east_asia_font = rFonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia')
                    
                    is_heiti = (
                        (font_name and '黑' in font_name) or
                        (east_asia_font and '黑' in east_asia_font) or
                        (font_name and 'Hei' in font_name) or
                        (east_asia_font and 'Hei' in east_asia_font)
                    )
                    if is_heiti:
                        heiti_found += 1
                    heiti_detail.append(f"'{text[:20]}': font='{font_name}', eastAsia='{east_asia_font}'")
        
        checks.append({
            "name": "level1_heading_uses_heiti",
            "passed": heiti_found >= 2,
            "detail": f"Found {heiti_found} level-1 headings with 黑体 font. Details: {'; '.join(heiti_detail[:6])}"
        })
    except Exception as e:
        checks.append({"name": "level1_heading_uses_heiti", "passed": False, "detail": str(e)})

    # ── Check 6: Level-2 heading uses 楷体 font ──────────────────────────────
    try:
        level2_patterns = ["（一）指导思想", "（二）基本原则", "（一）强化水资源刚性约束", "（一）加强组织领导"]
        kaiti_found = 0
        kaiti_detail = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            matched = any(p in text for p in level2_patterns)
            if matched and para.runs:
                for run in para.runs:
                    font_name = run.font.name
                    rPr = run._r.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
                    east_asia_font = None
                    if rPr is not None:
                        rFonts = rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts')
                        if rFonts is not None:
                            east_asia_font = rFonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia')
                    
                    is_kaiti = (
                        (font_name and '楷' in font_name) or
                        (east_asia_font and '楷' in east_asia_font) or
                        (font_name and 'Kai' in font_name) or
                        (east_asia_font and 'Kai' in east_asia_font)
                    )
                    if is_kaiti:
                        kaiti_found += 1
                    kaiti_detail.append(f"'{text[:20]}': font='{font_name}', eastAsia='{east_asia_font}'")
        
        checks.append({
            "name": "level2_heading_uses_kaiti",
            "passed": kaiti_found >= 2,
            "detail": f"Found {kaiti_found} level-2 headings with 楷体 font. Details: {'; '.join(kaiti_detail[:6])}"
        })
    except Exception as e:
        checks.append({"name": "level2_heading_uses_kaiti", "passed": False, "detail": str(e)})

    # ── Check 7: Body text uses 仿宋 ─────────────────────────────────────────
    try:
        fangsong_count = 0
        body_sample_texts = [
            "坚持以习近平新时代",
            "各区县要严格落实",
            "为深入贯彻落实",
        ]
        fangsong_detail = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            is_body = any(s in text for s in body_sample_texts)
            if is_body and para.runs:
                for run in para.runs:
                    font_name = run.font.name
                    rPr = run._r.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
                    east_asia_font = None
                    if rPr is not None:
                        rFonts = rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts')
                        if rFonts is not None:
                            east_asia_font = rFonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia')
                    
                    is_fangsong = (
                        (font_name and '仿' in font_name) or
                        (east_asia_font and '仿' in east_asia_font) or
                        (font_name and 'Fang' in font_name) or
                        (east_asia_font and 'Fang' in east_asia_font)
                    )
                    if is_fangsong:
                        fangsong_count += 1
                    fangsong_detail.append(f"font='{font_name}', eastAsia='{east_asia_font}'")
        
        checks.append({
            "name": "body_text_uses_fangsong",
            "passed": fangsong_count >= 1,
            "detail": f"Found {fangsong_count} body paragraphs with 仿宋 font. Details: {'; '.join(fangsong_detail[:4])}"
        })
    except Exception as e:
        checks.append({"name": "body_text_uses_fangsong", "passed": False, "detail": str(e)})

    # ── Check 8: Line spacing is 28pt (fixed/exact) ──────────────────────────
    try:
        from docx.oxml.ns import qn
        spacing_28pt_found = 0
        spacing_detail = []
        
        for para in doc.paragraphs:
            if not para.text.strip():
                continue
            pPr = para._p.find(qn('w:pPr'))
            if pPr is not None:
                spacing_elem = pPr.find(qn('w:spacing'))
                if spacing_elem is not None:
                    line_val = spacing_elem.get(qn('w:line'))
                    line_rule = spacing_elem.get(qn('w:lineRule'))
                    if line_val:
                        line_pt = int(line_val) / 20
                        if abs(line_pt - 28) < 1.0 and line_rule == 'exact':
                            spacing_28pt_found += 1
                        spacing_detail.append(f"line={line_pt}pt, rule={line_rule}")
        
        checks.append({
            "name": "line_spacing_28pt_exact",
            "passed": spacing_28pt_found >= 5,
            "detail": f"Found {spacing_28pt_found} paragraphs with exact 28pt line spacing. Samples: {'; '.join(spacing_detail[:5])}"
        })
    except Exception as e:
        checks.append({"name": "line_spacing_28pt_exact", "passed": False, "detail": str(e)})

    # ── Check 9: Level-1 heading punctuation (顿号 「、」) ──────────────────
    try:
        dun_hao_found = 0
        wrong_punct_found = 0
        level1_texts = []
        
        import re
        for para in doc.paragraphs:
            text = para.text.strip()
            if re.match(r'^[一二三四五六七八九十]+、', text):
                dun_hao_found += 1
                level1_texts.append(text[:30])
            # Wrong: level-1 with period or no punctuation
            if re.match(r'^[一二三四五六七八九十]+[^\、\s]', text):
                # Check it doesn't start with 顿号
                if not re.match(r'^[一二三四五六七八九十]+、', text):
                    wrong_punct_found += 1
        
        checks.append({
            "name": "level1_uses_dun_hao_punctuation",
            "passed": dun_hao_found >= 3 and wrong_punct_found == 0,
            "detail": f"Level-1 headings with 顿号: {dun_hao_found}, with wrong punctuation: {wrong_punct_found}. Texts: {level1_texts}"
        })
    except Exception as e:
        checks.append({"name": "level1_uses_dun_hao_punctuation", "passed": False, "detail": str(e)})

    # ── Check 10: Level-2 headings use NO trailing punctuation ───────────────
    try:
        import re
        level2_no_punct = 0
        level2_with_punct = 0
        level2_detail = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if re.match(r'^（[一二三四五六七八九十]+）', text):
                # Should NOT end with punctuation marks like 。，：、
                ends_with_punct = bool(re.search(r'[。，：、；！？]$', text))
                if ends_with_punct:
                    level2_with_punct += 1
                    level2_detail.append(f"BAD: {text[:30]}")
                else:
                    level2_no_punct += 1
                    level2_detail.append(f"OK: {text[:30]}")
        
        checks.append({
            "name": "level2_no_trailing_punctuation",
            "passed": level2_no_punct >= 2 and level2_with_punct == 0,
            "detail": f"Level-2 without trailing punct: {level2_no_punct}, with punct: {level2_with_punct}. {'; '.join(level2_detail[:6])}"
        })
    except Exception as e:
        checks.append({"name": "level2_no_trailing_punctuation", "passed": False, "detail": str(e)})

    # ── Compute score ────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)
    return checks, score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks, score = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crashed", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    overall_passed = score >= 0.75
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()