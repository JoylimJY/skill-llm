#!/usr/bin/env python3
"""
Evaluation script for the docx-formatter task.
Checks that the agent produced a properly formatted official Chinese document.
"""

import sys
import json
import traceback
from pathlib import Path

def main():
    workspace = Path(sys.argv[1])
    checks = []
    total_score = 0.0

    # ── Locate the output file ────────────────────────────────────────────────
    candidates = list(workspace.rglob("work_summary_2025.docx"))
    if not candidates:
        # also accept any docx that isn't the backup file
        candidates = [f for f in workspace.rglob("*.docx")
                      if "backup" not in f.name and "bad" not in f.name]

    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found: {candidates[0]}" if file_found else "No .docx output file found"
    })
    if not file_found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    docx_path = candidates[0]

    try:
        from docx import Document
        from docx.shared import Pt, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
        from docx.oxml.ns import qn

        doc = Document(str(docx_path))
        section = doc.sections[0]

        # ── CHECK 1: Page setup ───────────────────────────────────────────────
        try:
            w_ok = abs(section.page_width.inches  - 8.27) < 0.05
            h_ok = abs(section.page_height.inches - 11.69) < 0.05
            lm_ok = abs(section.left_margin.inches  - 1.25) < 0.05
            rm_ok = abs(section.right_margin.inches - 1.25) < 0.05
            tm_ok = abs(section.top_margin.inches   - 1.0)  < 0.05
            bm_ok = abs(section.bottom_margin.inches- 1.0)  < 0.05
            page_ok = all([w_ok, h_ok, lm_ok, rm_ok, tm_ok, bm_ok])
            checks.append({
                "name": "page_setup_A4_margins",
                "passed": page_ok,
                "detail": (f"page={section.page_width.inches:.2f}x{section.page_height.inches:.2f}in "
                           f"margins L={section.left_margin.inches:.2f} R={section.right_margin.inches:.2f} "
                           f"T={section.top_margin.inches:.2f} B={section.bottom_margin.inches:.2f}")
            })
            if page_ok:
                total_score += 0.10
        except Exception as e:
            checks.append({"name": "page_setup_A4_margins", "passed": False, "detail": str(e)})

        # ── Collect all paragraphs ────────────────────────────────────────────
        all_paras = list(doc.paragraphs)

        # ── CHECK 2: Title paragraph uses 方正小标宋简体, 2号 (22pt), centered ─
        try:
            title_para = None
            for p in all_paras:
                text = p.text.strip()
                if '北阳县农业农村局' in text and '工作总结' in text:
                    title_para = p
                    break

            if title_para is None:
                checks.append({"name": "title_font_and_align",
                               "passed": False, "detail": "Title paragraph not found"})
            else:
                runs = [r for r in title_para.runs if r.text.strip()]
                font_ok = False
                size_ok = False
                if runs:
                    r = runs[0]
                    # Check east-asia font via XML
                    rPr = r._r.find(qn('w:rPr'))
                    ea_font = ''
                    if rPr is not None:
                        rFonts = rPr.find(qn('w:rFonts'))
                        if rFonts is not None:
                            ea_font = rFonts.get(qn('w:eastAsia'), '') or rFonts.get(qn('w:ascii'), '')
                    font_ok = '方正小标宋' in ea_font or '方正小标宋简体' in (r.font.name or '')
                    size_ok = r.font.size is not None and abs(r.font.size.pt - 22) < 1.0

                align_ok = title_para.paragraph_format.alignment in (
                    WD_ALIGN_PARAGRAPH.CENTER, None  # None can inherit center
                )
                # also check via XML
                pPr = title_para._p.find(qn('w:pPr'))
                if pPr is not None:
                    jc = pPr.find(qn('w:jc'))
                    if jc is not None and jc.get(qn('w:val')) == 'center':
                        align_ok = True

                title_ok = font_ok and size_ok
                checks.append({
                    "name": "title_font_fangsong_2hao_centered",
                    "passed": title_ok,
                    "detail": f"font_ok={font_ok}(ea='{ea_font}') size_ok={size_ok}(pt={runs[0].font.size.pt if runs and runs[0].font.size else 'None'}) align_ok={align_ok}"
                })
                if title_ok:
                    total_score += 0.15
        except Exception as e:
            checks.append({"name": "title_font_fangsong_2hao_centered",
                           "passed": False, "detail": traceback.format_exc()})

        # ── CHECK 3: H1 paragraphs use 黑体 3号 ───────────────────────────────
        try:
            h1_paras = []
            # H1 should contain Chinese section numbers like 一、二、三
            h1_markers = ['全面推进粮食安全', '扎实推进乡村振兴', '存在的主要问题']
            for p in all_paras:
                for marker in h1_markers:
                    if marker in p.text:
                        h1_paras.append(p)
                        break

            h1_ok = True
            h1_details = []
            for p in h1_paras:
                runs = [r for r in p.runs if r.text.strip()]
                if not runs:
                    h1_ok = False
                    h1_details.append(f"'{p.text[:20]}' has no runs")
                    continue
                r = runs[0]
                rPr = r._r.find(qn('w:rPr'))
                ea_font = ''
                if rPr is not None:
                    rFonts = rPr.find(qn('w:rFonts'))
                    if rFonts is not None:
                        ea_font = rFonts.get(qn('w:eastAsia'), '') or rFonts.get(qn('w:ascii'), '')
                font_ok = '黑体' in ea_font or '黑体' in (r.font.name or '')
                size_ok = r.font.size is not None and abs(r.font.size.pt - 16) < 1.0
                h1_details.append(f"'{p.text[:15]}' font={ea_font or r.font.name} size={r.font.size.pt if r.font.size else 'None'}")
                if not (font_ok and size_ok):
                    h1_ok = False

            found_h1 = len(h1_paras) >= 2
            checks.append({
                "name": "h1_heiti_3hao",
                "passed": found_h1 and h1_ok,
                "detail": f"found={len(h1_paras)} paras, ok={h1_ok}: " + "; ".join(h1_details)
            })
            if found_h1 and h1_ok:
                total_score += 0.15
        except Exception as e:
            checks.append({"name": "h1_heiti_3hao", "passed": False, "detail": traceback.format_exc()})

        # ── CHECK 4: H2 paragraphs use 楷体_GB2312 3号 ───────────────────────
        try:
            h2_paras = []
            h2_markers = ['落实耕地保护', '强化农业科技', '巩固拓展脱贫', '推进农村人居', '存在的主要问题', '下一步工作']
            for p in all_paras:
                for marker in h2_markers:
                    if marker in p.text:
                        h2_paras.append(p)
                        break

            h2_ok = True
            h2_details = []
            for p in h2_paras:
                runs = [r for r in p.runs if r.text.strip()]
                if not runs:
                    continue
                r = runs[0]
                rPr = r._r.find(qn('w:rPr'))
                ea_font = ''
                if rPr is not None:
                    rFonts = rPr.find(qn('w:rFonts'))
                    if rFonts is not None:
                        ea_font = rFonts.get(qn('w:eastAsia'), '') or rFonts.get(qn('w:ascii'), '')
                font_ok = '楷体' in ea_font or '楷体' in (r.font.name or '')
                size_ok = r.font.size is not None and abs(r.font.size.pt - 16) < 1.0
                h2_details.append(f"'{p.text[:15]}' font={ea_font or r.font.name} size={r.font.size.pt if r.font.size else 'None'}")
                if not (font_ok and size_ok):
                    h2_ok = False

            found_h2 = len(h2_paras) >= 2
            checks.append({
                "name": "h2_kaiti_3hao",
                "passed": found_h2 and h2_ok,
                "detail": f"found={len(h2_paras)}: " + "; ".join(h2_details)
            })
            if found_h2 and h2_ok:
                total_score += 0.15
        except Exception as e:
            checks.append({"name": "h2_kaiti_3hao", "passed": False, "detail": traceback.format_exc()})

        # ── CHECK 5: Body paragraphs use 仿宋_GB2312 3号 ─────────────────────
        try:
            body_paras = []
            body_markers = ['全县耕地总面积', '全年推广优质', '持续开展防返贫', '完成农村厕所']
            for p in all_paras:
                for marker in body_markers:
                    if marker in p.text:
                        body_paras.append(p)
                        break

            body_ok = True
            body_details = []
            for p in body_paras:
                runs = [r for r in p.runs if r.text.strip()]
                if not runs:
                    continue
                # Find a run that is NOT bold (bold runs are h3 prefix)
                plain_runs = [r for r in runs if not r.font.bold]
                if not plain_runs:
                    plain_runs = runs
                r = plain_runs[0]
                rPr = r._r.find(qn('w:rPr'))
                ea_font = ''
                if rPr is not None:
                    rFonts = rPr.find(qn('w:rFonts'))
                    if rFonts is not None:
                        ea_font = rFonts.get(qn('w:eastAsia'), '') or rFonts.get(qn('w:ascii'), '')
                font_ok = '仿宋' in ea_font or '仿宋' in (r.font.name or '')
                size_ok = r.font.size is not None and abs(r.font.size.pt - 16) < 1.0
                body_details.append(f"'{p.text[:20]}' font={ea_font or r.font.name} size={r.font.size.pt if r.font.size else 'None'}")
                if not (font_ok and size_ok):
                    body_ok = False

            found_body = len(body_paras) >= 2
            checks.append({
                "name": "body_fangsong_3hao",
                "passed": found_body and body_ok,
                "detail": f"found={len(body_paras)}: " + "; ".join(body_details)
            })
            if found_body and body_ok:
                total_score += 0.15
        except Exception as e:
            checks.append({"name": "body_fangsong_3hao", "passed": False, "detail": traceback.format_exc()})

        # ── CHECK 6: Line spacing is EXACTLY 28pt for body paragraphs ─────────
        try:
            spacing_ok = True
            spacing_details = []
            for p in all_paras:
                if not p.text.strip():
                    continue
                pf = p.paragraph_format
                if pf.line_spacing is not None:
                    ls_pt = pf.line_spacing.pt if hasattr(pf.line_spacing, 'pt') else None
                    if ls_pt is not None and abs(ls_pt - 28) > 2.0:
                        spacing_ok = False
                        spacing_details.append(f"'{p.text[:20]}' spacing={ls_pt}pt")
                # also check XML
                pPr = p._p.find(qn('w:pPr'))
                if pPr is not None:
                    spacing = pPr.find(qn('w:spacing'))
                    if spacing is not None:
                        line_val = spacing.get(qn('w:line'))
                        line_rule = spacing.get(qn('w:lineRule'))
                        if line_val and line_rule == 'exact':
                            # value in twentieths of a point
                            line_pt = int(line_val) / 20.0
                            if abs(line_pt - 28) > 2.0:
                                spacing_ok = False
                                spacing_details.append(f"'{p.text[:20]}' XML spacing={line_pt}pt rule={line_rule}")

            checks.append({
                "name": "line_spacing_28pt_fixed",
                "passed": spacing_ok,
                "detail": "All checked" if not spacing_details else "; ".join(spacing_details[:5])
            })
            if spacing_ok:
                total_score += 0.10
        except Exception as e:
            checks.append({"name": "line_spacing_28pt_fixed", "passed": False, "detail": traceback.format_exc()})

        # ── CHECK 7: First-line indent ~32pt for body paragraphs ──────────────
        try:
            indent_ok_count = 0
            indent_total = 0
            for p in all_paras:
                if not p.text.strip():
                    continue
                # Only check body/h3 paragraphs (not headings/title/author)
                # Heuristic: check paragraphs with substantial text
                if len(p.text.strip()) < 10:
                    continue
                pf = p.paragraph_format
                pPr = p._p.find(qn('w:pPr'))
                ind_val = None
                if pPr is not None:
                    ind = pPr.find(qn('w:ind'))
                    if ind is not None:
                        fi = ind.get(qn('w:firstLine'))
                        if fi:
                            ind_val = int(fi) / 20.0  # twips to pt

                if ind_val is not None:
                    indent_total += 1
                    if abs(ind_val - 32) < 5:
                        indent_ok_count += 1

            indent_ok = indent_total == 0 or (indent_ok_count / indent_total >= 0.5)
            checks.append({
                "name": "first_line_indent_32pt",
                "passed": indent_ok,
                "detail": f"{indent_ok_count}/{indent_total} body paragraphs have ~32pt first-line indent"
            })
            if indent_ok and indent_total > 0:
                total_score += 0.05
        except Exception as e:
            checks.append({"name": "first_line_indent_32pt", "passed": False, "detail": traceback.format_exc()})

        # ── CHECK 8: Author/signature block present ───────────────────────────
        try:
            author_text = '\n'.join(p.text for p in all_paras)
            has_org  = '北阳县农业农村局' in author_text
            has_date = '2025年12月31日' in author_text or '2025年' in author_text

            # Find the author paragraphs (near end)
            author_paras = [p for p in all_paras
                            if '北阳县农业农村局' in p.text or '2025年12月' in p.text]
            author_centered = False
            for p in author_paras:
                pPr = p._p.find(qn('w:pPr'))
                if pPr is not None:
                    jc = pPr.find(qn('w:jc'))
                    if jc is not None and jc.get(qn('w:val')) == 'center':
                        author_centered = True
                        break

            author_ok = has_org and has_date
            checks.append({
                "name": "author_signature_block",
                "passed": author_ok,
                "detail": f"has_org={has_org} has_date={has_date} centered={author_centered}"
            })
            if author_ok:
                total_score += 0.05
        except Exception as e:
            checks.append({"name": "author_signature_block", "passed": False, "detail": traceback.format_exc()})

        # ── CHECK 9: Page footer contains PAGE field (page number) ────────────
        try:
            footer = section.footer
            footer_text = ' '.join(p.text for p in footer.paragraphs)
            # Check for fldChar/instrText PAGE in XML
            footer_xml = footer._element.xml
            has_page_field = 'PAGE' in footer_xml or 'fldChar' in footer_xml
            checks.append({
                "name": "footer_page_number",
                "passed": has_page_field,
                "detail": f"Footer XML contains PAGE field: {has_page_field}"
            })
            if has_page_field:
                total_score += 0.05
        except Exception as e:
            checks.append({"name": "footer_page_number", "passed": False, "detail": traceback.format_exc()})

        # ── CHECK 10: H3 inline bold prefix present ───────────────────────────
        try:
            h3_found = False
            h3_detail = "No h3 inline paragraph found"
            for p in all_paras:
                if '技术推广成效' in p.text or '整治重点' in p.text:
                    runs = [r for r in p.runs if r.text.strip()]
                    if runs:
                        bold_runs = [r for r in runs if r.font.bold]
                        plain_runs = [r for r in runs if not r.font.bold]
                        if bold_runs and plain_runs:
                            h3_found = True
                            h3_detail = f"Found inline bold prefix: '{bold_runs[0].text[:20]}' + plain: '{plain_runs[0].text[:20]}'"
                            break

            checks.append({
                "name": "h3_inline_bold_prefix",
                "passed": h3_found,
                "detail": h3_detail
            })
            if h3_found:
                total_score += 0.05
        except Exception as e:
            checks.append({"name": "h3_inline_bold_prefix", "passed": False, "detail": traceback.format_exc()})

        # ── CHECK 11: Document has substantial content (all 3 major sections) ──
        try:
            full_text = '\n'.join(p.text for p in all_paras)
            content_markers = [
                '粮食安全',
                '乡村振兴',
                '存在',
                '耕地',
                '脱贫',
            ]
            found_markers = [m for m in content_markers if m in full_text]
            content_ok = len(found_markers) >= 4
            checks.append({
                "name": "document_content_completeness",
                "passed": content_ok,
                "detail": f"Found {len(found_markers)}/{len(content_markers)} content markers: {found_markers}"
            })
            if content_ok:
                total_score += 0.05
        except Exception as e:
            checks.append({"name": "document_content_completeness", "passed": False,
                           "detail": traceback.format_exc()})

    except Exception as e:
        checks.append({"name": "docx_parse_error", "passed": False,
                       "detail": f"Failed to open/parse docx: {traceback.format_exc()}"})

    passed_checks = [c for c in checks if c["passed"]]
    overall_passed = (total_score >= 0.5)  # need at least half the weighted checks

    print(json.dumps({
        "passed": overall_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()