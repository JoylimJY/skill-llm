#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluation script for the official-document task.
Usage: python eval_script.py /workspace
"""
import sys
import json
import traceback
from pathlib import Path

def run_checks(workspace: Path):
    checks = []
    total_score = 0.0

    # ── helper ──────────────────────────────────────────────────────────────
    def add(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── locate the output file ───────────────────────────────────────────────
    target_filename = "county_procurement_notice_2026.docx"
    found = list(workspace.rglob(target_filename))

    if not found:
        checks.append({
            "name": "file_exists",
            "passed": False,
            "detail": f"File '{target_filename}' not found anywhere under {workspace}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    docx_path = found[0]
    total_score += add("file_exists", True, f"Found at {docx_path}")

    # ── load document ────────────────────────────────────────────────────────
    try:
        from docx import Document
        from docx.shared import Pt, Cm, Emu
        from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
        doc = Document(str(docx_path))
    except Exception as e:
        checks.append({"name": "document_loadable", "passed": False,
                        "detail": f"Failed to open docx: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    total_score += add("document_loadable", True, "Document opened successfully")

    paragraphs = doc.paragraphs

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 1: Page margins (GB/T 9704-2012)
    # top=3.7cm, bottom=3.5cm, left=2.8cm, right=2.6cm
    # ═══════════════════════════════════════════════════════════════════════
    try:
        section = doc.sections[0]
        top_cm    = section.top_margin.cm
        bottom_cm = section.bottom_margin.cm
        left_cm   = section.left_margin.cm
        right_cm  = section.right_margin.cm

        margin_ok = (
            abs(top_cm    - 3.7) < 0.15 and
            abs(bottom_cm - 3.5) < 0.15 and
            abs(left_cm   - 2.8) < 0.15 and
            abs(right_cm  - 2.6) < 0.15
        )
        detail = (f"top={top_cm:.2f}cm(exp 3.7), bottom={bottom_cm:.2f}cm(exp 3.5), "
                  f"left={left_cm:.2f}cm(exp 2.8), right={right_cm:.2f}cm(exp 2.6)")
        total_score += add("page_margins_correct", margin_ok, detail, weight=2.0)
    except Exception as e:
        total_score += add("page_margins_correct", False, f"Exception: {e}", weight=2.0)

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 2: 发文字号 uses 六角括号 〔〕 (NOT 【】 or [] or （）)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        full_text = "\n".join(p.text for p in paragraphs)
        
        # Must contain the six-corner brackets version
        correct_code = "县采购办〔2026〕12号"
        has_correct = correct_code in full_text
        
        # Must NOT use wrong brackets around the year
        import re
        wrong_bracket_pattern = re.compile(r"县采购办[【\[\(（]2026[】\]\)）]12号")
        has_wrong = bool(wrong_bracket_pattern.search(full_text))
        
        passed = has_correct and not has_wrong
        detail = (f"correct_code_present={has_correct}, "
                  f"wrong_bracket_used={has_wrong}. "
                  f"Must use 〔〕 not 【】or[]")
        total_score += add("document_code_six_corner_brackets", passed, detail, weight=3.0)
    except Exception as e:
        total_score += add("document_code_six_corner_brackets", False, f"Exception: {e}", weight=3.0)

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 3: 公文标题 font = 方正小标宋简体, 22pt, NOT bold, centered
    # ═══════════════════════════════════════════════════════════════════════
    try:
        title_text = "关于开展2026年度政府集中采购工作的通知"
        title_para = None
        for p in paragraphs:
            if title_text in p.text:
                title_para = p
                break
        
        if title_para is None:
            total_score += add("title_formatting", False,
                               f"Title paragraph not found: '{title_text}'", weight=3.0)
        else:
            # Check alignment
            align_ok = (title_para.alignment == WD_ALIGN_PARAGRAPH.CENTER)
            
            # Check runs for font name and size
            font_name_ok = False
            font_size_ok = False
            bold_ok = True  # should NOT be bold
            
            for run in title_para.runs:
                if run.text.strip():
                    fn = run.font.name or ""
                    fs = run.font.size
                    # Check paragraph-level format if run doesn't override
                    pf = title_para.style.font if title_para.style else None
                    
                    if "小标宋" in fn or "方正小标宋" in fn:
                        font_name_ok = True
                    if fs and abs(fs.pt - 22) < 0.5:
                        font_size_ok = True
                    if run.bold:
                        bold_ok = False
            
            # Also check paragraph format for font size via XML if runs don't reveal it
            if not font_size_ok:
                from lxml import etree
                xml_str = title_para._element.xml
                if "2794" in xml_str or "314" in xml_str:  # 22pt = 314 half-pts? Actually 22*2=44 twips; in OOXML sz is in half-pts so 22pt = sz 44
                    font_size_ok = True
                # Also check sz element
                sz_matches = re.findall(r'w:sz[^W]*?w:val="(\d+)"', xml_str)
                for m in sz_matches:
                    if abs(int(m)/2 - 22) < 0.5:
                        font_size_ok = True
            
            passed = align_ok and font_name_ok and font_size_ok and bold_ok
            detail = (f"align_center={align_ok}, font_contains_小标宋={font_name_ok}, "
                      f"size_22pt={font_size_ok}, not_bold={bold_ok}")
            total_score += add("title_formatting", passed, detail, weight=3.0)
    except Exception as e:
        total_score += add("title_formatting", False, f"Exception: {traceback.format_exc()}", weight=3.0)

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 4: Line spacing = fixed 28.5pt across body paragraphs
    # ═══════════════════════════════════════════════════════════════════════
    try:
        from lxml import etree
        target_spacing_twips = 28.5 * 20  # 570 twips
        # Accept 28 to 29 pt range
        lo = 28 * 20
        hi = 29 * 20

        body_paras_with_spacing = []
        for p in paragraphs:
            if not p.text.strip():
                continue
            pf = p.paragraph_format
            ls = pf.line_spacing
            ls_rule = pf.line_spacing_rule
            if ls is not None:
                # ls is in EMU if it's a fixed value
                try:
                    ls_pt = ls.pt
                    body_paras_with_spacing.append((p.text[:20], ls_pt, ls_rule))
                except:
                    pass

        # Check that majority of non-empty paragraphs have ~28.5pt fixed spacing
        fixed_count = 0
        for _, ls_pt, ls_rule in body_paras_with_spacing:
            if ls_rule == WD_LINE_SPACING.EXACTLY and abs(ls_pt - 28.5) < 1.5:
                fixed_count += 1

        if not body_paras_with_spacing:
            # Try XML approach
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            fixed_count_xml = 0
            total_checked = 0
            for p in paragraphs:
                if not p.text.strip():
                    continue
                total_checked += 1
                el = p._element
                spacing_els = el.findall('.//w:spacing', ns)
                for se in spacing_els:
                    line_val = se.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}line')
                    line_rule = se.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}lineRule')
                    if line_val and line_rule == 'exact':
                        lv = int(line_val)
                        if lo <= lv <= hi:
                            fixed_count_xml += 1
            
            passed = fixed_count_xml > 0 and (total_checked == 0 or fixed_count_xml / max(total_checked, 1) > 0.3)
            detail = f"XML check: {fixed_count_xml}/{total_checked} paragraphs have fixed ~28.5pt spacing"
        else:
            passed = (fixed_count > 0 and 
                      fixed_count / len(body_paras_with_spacing) > 0.3)
            detail = (f"{fixed_count}/{len(body_paras_with_spacing)} paragraphs "
                      f"have fixed ~28.5pt line spacing")
        
        total_score += add("line_spacing_fixed_28_5pt", passed, detail, weight=2.0)
    except Exception as e:
        total_score += add("line_spacing_fixed_28_5pt", False, f"Exception: {traceback.format_exc()}", weight=2.0)

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 5: 一级标题 uses 黑体, NOT bold, 16pt
    # ═══════════════════════════════════════════════════════════════════════
    try:
        h1_texts = [
            "一、工作目标",
            "二、主要任务",
            "三、工作要求"
        ]
        found_h1 = []
        for p in paragraphs:
            for ht in h1_texts:
                if ht in p.text:
                    found_h1.append(p)
                    break

        if not found_h1:
            total_score += add("h1_heading_font_heiti", False,
                               "No 一级标题 paragraphs found", weight=2.0)
        else:
            heiti_ok_count = 0
            for p in found_h1:
                for run in p.runs:
                    if run.text.strip():
                        fn = run.font.name or ""
                        if "黑体" in fn or "Heiti" in fn or "黑" in fn:
                            heiti_ok_count += 1
                            break
            passed = heiti_ok_count == len(found_h1)
            detail = f"{heiti_ok_count}/{len(found_h1)} 一级标题 paragraphs use 黑体"
            total_score += add("h1_heading_font_heiti", passed, detail, weight=2.0)
    except Exception as e:
        total_score += add("h1_heading_font_heiti", False, f"Exception: {e}", weight=2.0)

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 6: 二级标题 uses 楷体_GB2312
    # ═══════════════════════════════════════════════════════════════════════
    try:
        h2_texts = [
            "（一）编制采购计划",
            "（二）规范采购程序",
        ]
        found_h2 = []
        for p in paragraphs:
            for ht in h2_texts:
                if ht in p.text:
                    found_h2.append(p)
                    break

        if not found_h2:
            total_score += add("h2_heading_font_kaiti", False,
                               "No 二级标题 paragraphs found", weight=1.5)
        else:
            kaiti_ok = 0
            for p in found_h2:
                for run in p.runs:
                    if run.text.strip():
                        fn = run.font.name or ""
                        if "楷体" in fn or "KaiTi" in fn or "楷" in fn:
                            kaiti_ok += 1
                            break
            passed = kaiti_ok == len(found_h2)
            detail = f"{kaiti_ok}/{len(found_h2)} 二级标题 paragraphs use 楷体"
            total_score += add("h2_heading_font_kaiti", passed, detail, weight=1.5)
    except Exception as e:
        total_score += add("h2_heading_font_kaiti", False, f"Exception: {e}", weight=1.5)

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 7: Spacing structure — 落款前 has ≥3 blank lines
    # ═══════════════════════════════════════════════════════════════════════
    try:
        issuer_text = "XX县人民政府采购管理办公室"
        issuer_idx = None
        for i, p in enumerate(paragraphs):
            if issuer_text in p.text and i > len(paragraphs) // 2:
                issuer_idx = i
                break

        if issuer_idx is None:
            total_score += add("spacing_before_signature", False,
                               f"Issuer/落款 paragraph not found: '{issuer_text}'", weight=1.5)
        else:
            # Count blank lines immediately before issuer
            blank_count = 0
            idx = issuer_idx - 1
            while idx >= 0 and not paragraphs[idx].text.strip():
                blank_count += 1
                idx -= 1
            passed = blank_count >= 3
            detail = f"Found {blank_count} blank lines before 落款 (need ≥3)"
            total_score += add("spacing_before_signature", passed, detail, weight=1.5)
    except Exception as e:
        total_score += add("spacing_before_signature", False, f"Exception: {e}", weight=1.5)

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 8: Attachments present with correct format
    # ═══════════════════════════════════════════════════════════════════════
    try:
        full_text = "\n".join(p.text for p in paragraphs)
        has_attach1 = "政府集中采购计划申报表" in full_text
        has_attach2 = "2026年集中采购目录及限额标准" in full_text
        # Should have numbered format for 2 attachments
        has_numbered = ("1." in full_text or "1、" in full_text) and (
                        "2." in full_text or "2、" in full_text)
        passed = has_attach1 and has_attach2
        detail = (f"attach1={has_attach1}, attach2={has_attach2}, "
                  f"numbered_format={has_numbered}")
        total_score += add("attachments_present", passed, detail, weight=1.5)
    except Exception as e:
        total_score += add("attachments_present", False, f"Exception: {e}", weight=1.5)

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 9: 联系方式 is present with correct format hint
    # ═══════════════════════════════════════════════════════════════════════
    try:
        full_text = "\n".join(p.text for p in paragraphs)
        has_contact_person = "李明" in full_text
        has_phone = "0912-8765432" in full_text
        has_address = "B座304室" in full_text
        # Should be wrapped in fullwidth parentheses or regular parens
        has_paren = "联系人：李明" in full_text or "联系人:李明" in full_text
        passed = has_contact_person and has_phone and has_address
        detail = (f"person={has_contact_person}, phone={has_phone}, "
                  f"address={has_address}, paren_format={has_paren}")
        total_score += add("contact_info_present", passed, detail, weight=1.0)
    except Exception as e:
        total_score += add("contact_info_present", False, f"Exception: {e}", weight=1.0)

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 10: Body text font is 仿宋 (for normal body paragraphs)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        body_snippet = "坚持公开、公平、公正原则"
        body_para = None
        for p in paragraphs:
            if body_snippet in p.text:
                body_para = p
                break
        if body_para is None:
            total_score += add("body_font_fangsong", False,
                               "Body paragraph not found", weight=1.5)
        else:
            fangsong_ok = False
            size_ok = False
            for run in body_para.runs:
                if run.text.strip():
                    fn = run.font.name or ""
                    fs = run.font.size
                    if "仿宋" in fn or "FangSong" in fn:
                        fangsong_ok = True
                    if fs and abs(fs.pt - 16) < 0.5:
                        size_ok = True
            passed = fangsong_ok and size_ok
            detail = f"body_font_contains_仿宋={fangsong_ok}, size_16pt={size_ok}"
            total_score += add("body_font_fangsong", passed, detail, weight=1.5)
    except Exception as e:
        total_score += add("body_font_fangsong", False, f"Exception: {e}", weight=1.5)

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 11: 发文字号 paragraph is right-aligned
    # ═══════════════════════════════════════════════════════════════════════
    try:
        code_text = "县采购办〔2026〕12号"
        code_para = None
        for p in paragraphs:
            if code_text in p.text:
                code_para = p
                break
        if code_para is None:
            total_score += add("doc_code_right_aligned", False,
                               "发文字号 paragraph not found", weight=1.0)
        else:
            align_ok = (code_para.alignment == WD_ALIGN_PARAGRAPH.RIGHT)
            detail = f"alignment={code_para.alignment} (expected RIGHT)"
            total_score += add("doc_code_right_aligned", align_ok, detail, weight=1.0)
    except Exception as e:
        total_score += add("doc_code_right_aligned", False, f"Exception: {e}", weight=1.0)

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 12: Spacing between 发文字号 → 标题 = 2 blank lines
    # ═══════════════════════════════════════════════════════════════════════
    try:
        code_text = "县采购办〔2026〕12号"
        title_text = "关于开展2026年度政府集中采购工作的通知"
        code_idx = None
        title_idx = None
        for i, p in enumerate(paragraphs):
            if code_text in p.text and code_idx is None:
                code_idx = i
            if title_text in p.text and title_idx is None:
                title_idx = i
        
        if code_idx is None or title_idx is None:
            total_score += add("spacing_code_to_title", False,
                               f"Could not locate code_idx={code_idx}, title_idx={title_idx}", weight=1.5)
        else:
            # Count blank paragraphs between them
            blank_count = 0
            for i in range(code_idx + 1, title_idx):
                if not paragraphs[i].text.strip():
                    blank_count += 1
            passed = blank_count == 2
            detail = f"Blank lines between 发文字号 and 标题: {blank_count} (expected 2)"
            total_score += add("spacing_code_to_title", passed, detail, weight=1.5)
    except Exception as e:
        total_score += add("spacing_code_to_title", False, f"Exception: {e}", weight=1.5)

    # ═══════════════════════════════════════════════════════════════════════
    # Compute final score (normalize to 0-1)
    # Max possible weight: 1+1+2+3+3+2+2+1.5+1.5+1.5+1.0+1.5+1.0+1.5 = 23.5
    # ═══════════════════════════════════════════════════════════════════════
    max_weight = 23.5
    normalized_score = min(1.0, total_score / max_weight)
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": round(normalized_score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    result = run_checks(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))