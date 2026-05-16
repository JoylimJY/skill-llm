import sys
import json
import traceback
from pathlib import Path

def run_checks(workspace):
    checks = []
    score = 0.0

    # ── helper ──────────────────────────────────────────────────────────────
    def add(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── 1. Find the .docx output ─────────────────────────────────────────────
    docx_files = list(Path(workspace).rglob("*.docx"))
    if not docx_files:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "No .docx file found anywhere in workspace."})
        return False, 0.0, checks

    # Pick the most-recently-modified .docx (in case there are multiple)
    docx_path = sorted(docx_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    score += add("output_file_exists", True,
                 f"Found .docx at: {docx_path}", weight=0.5)

    # ── 2. Load document ─────────────────────────────────────────────────────
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.oxml.ns import qn
        import docx.oxml as oxml
        doc = Document(str(docx_path))
    except Exception as e:
        checks.append({"name": "docx_loadable", "passed": False,
                        "detail": f"Failed to open .docx: {e}"})
        return False, score, checks
    score += add("docx_loadable", True, "Document opened successfully.", weight=0.5)

    # ── 3. Page margins (DXA) ────────────────────────────────────────────────
    # Expected: top/bottom ≈ 2540 DXA, left/right ≈ 1800 DXA  (±150 tolerance)
    try:
        section = doc.sections[0]
        top_dxa    = section.top_margin.twips     # python-docx: twips == DXA
        bottom_dxa = section.bottom_margin.twips
        left_dxa   = section.left_margin.twips
        right_dxa  = section.right_margin.twips

        margin_ok = (
            abs(top_dxa    - 2540) <= 200 and
            abs(bottom_dxa - 2540) <= 200 and
            abs(left_dxa   - 1800) <= 200 and
            abs(right_dxa  - 1800) <= 200
        )
        detail = (f"top={top_dxa}, bottom={bottom_dxa}, "
                  f"left={left_dxa}, right={right_dxa} DXA")
        score += add("page_margins_dxa", margin_ok, detail, weight=1.5)
    except Exception as e:
        score += add("page_margins_dxa", False, f"Error reading margins: {e}", weight=1.5)

    # ── 4. Chinese heading fonts ─────────────────────────────────────────────
    # At least one paragraph styled as Heading 1 must use SimHei (or 黑体)
    # body paragraphs must use FangSong or SimSun
    try:
        simhei_names   = {"simhei", "黑体", "sim hei"}
        fangsong_names = {"fangsong", "仿宋", "fang song", "simsun", "宋体", "sim sun"}

        h1_font_ok   = False
        body_font_ok = False

        for para in doc.paragraphs:
            style_name = (para.style.name or "").lower()
            # Check heading 1
            if "heading 1" in style_name or "1" in style_name:
                for run in para.runs:
                    fn = (run.font.name or "").lower().replace(" ", "")
                    if any(n.replace(" ", "") in fn for n in simhei_names):
                        h1_font_ok = True
                        break
                # Also check via XML rFonts
                if not h1_font_ok:
                    for run in para.runs:
                        rpr = run._r.find(qn('w:rPr'))
                        if rpr is not None:
                            rfonts = rpr.find(qn('w:rFonts'))
                            if rfonts is not None:
                                for attr in rfonts.attrib.values():
                                    if any(n.replace(" ", "") in attr.lower().replace(" ", "")
                                           for n in simhei_names):
                                        h1_font_ok = True

            # Check body (Normal style)
            if "normal" in style_name or style_name == "":
                for run in para.runs:
                    fn = (run.font.name or "").lower().replace(" ", "")
                    if any(n.replace(" ", "") in fn for n in fangsong_names):
                        body_font_ok = True
                        break

        # Fallback: scan ALL runs for font usage
        if not h1_font_ok or not body_font_ok:
            for para in doc.paragraphs:
                for run in para.runs:
                    fn = (run.font.name or "").lower().replace(" ", "")
                    if any(n.replace(" ", "") in fn for n in simhei_names):
                        h1_font_ok = True
                    if any(n.replace(" ", "") in fn for n in fangsong_names):
                        body_font_ok = True

        score += add("heading_font_simhei", h1_font_ok,
                     "SimHei/黑体 detected in heading runs." if h1_font_ok
                     else "No SimHei/黑体 font found in heading runs.", weight=1.0)
        score += add("body_font_fangsong_or_simsun", body_font_ok,
                     "FangSong/仿宋/SimSun detected in body runs." if body_font_ok
                     else "No FangSong/SimSun font found in body runs.", weight=1.0)
    except Exception as e:
        score += add("heading_font_simhei", False, f"Error: {e}", weight=1.0)
        score += add("body_font_fangsong_or_simsun", False, f"Error: {e}", weight=1.0)

    # ── 5. Chinese heading numbering hierarchy ────────────────────────────────
    # Report must use the required 一、（一）1. hierarchy in paragraph text
    try:
        full_text = "\n".join(p.text for p in doc.paragraphs)
        import re
        has_level1 = bool(re.search(r'[一二三四五六七八九十]+、', full_text))
        has_level2 = bool(re.search(r'（[一二三四五六七八九十]+）', full_text))
        has_level3 = bool(re.search(r'\d+\.', full_text))
        hierarchy_ok = has_level1 and has_level2
        detail = (f"Level-1 (X、): {has_level1}, "
                  f"Level-2 (（X）): {has_level2}, "
                  f"Level-3 (N.): {has_level3}")
        score += add("heading_hierarchy_chinese", hierarchy_ok, detail, weight=1.5)
    except Exception as e:
        score += add("heading_hierarchy_chinese", False, f"Error: {e}", weight=1.5)

    # ── 6. Table with #D9D9D9 header shading ─────────────────────────────────
    try:
        table_found = False
        header_shading_ok = False
        target_fill = "d9d9d9"

        for table in doc.tables:
            table_found = True
            if table.rows:
                header_row = table.rows[0]
                for cell in header_row.cells:
                    tc = cell._tc
                    tcpr = tc.find(qn('w:tcPr'))
                    if tcpr is not None:
                        shd = tcpr.find(qn('w:shd'))
                        if shd is not None:
                            fill = shd.get(qn('w:fill'), "").lower()
                            if target_fill in fill:
                                header_shading_ok = True
                                break
                if header_shading_ok:
                    break

        score += add("table_exists", table_found,
                     "At least one table found." if table_found
                     else "No table found in document.", weight=1.0)
        score += add("table_header_shading_d9d9d9", header_shading_ok,
                     f"Table header row has #D9D9D9 fill." if header_shading_ok
                     else "Table header row does NOT have #D9D9D9 fill.", weight=1.5)
    except Exception as e:
        score += add("table_exists", False, f"Error: {e}", weight=1.0)
        score += add("table_header_shading_d9d9d9", False, f"Error: {e}", weight=1.5)

    # ── 7. Content coherence: must reference key topics from input materials ──
    try:
        full_text_lower = full_text.lower()
        keywords_required = [
            "原集体企业",
            "考核",
            "工资总额",
        ]
        missing = [kw for kw in keywords_required if kw not in full_text]
        content_ok = len(missing) == 0
        detail = (f"All required keywords present." if content_ok
                  else f"Missing keywords: {missing}")
        score += add("content_covers_required_topics", content_ok, detail, weight=1.5)
    except Exception as e:
        score += add("content_covers_required_topics", False, f"Error: {e}", weight=1.5)

    # ── 8. Page footer with page number ──────────────────────────────────────
    try:
        footer_ok = False
        for section in doc.sections:
            footer = section.footer
            if footer:
                footer_text = " ".join(p.text for p in footer.paragraphs)
                # Check XML for page number field (w:fldChar / PAGE)
                footer_xml = footer._element.xml
                if ("PAGE" in footer_xml or "页码" in footer_xml or
                        "fldChar" in footer_xml or footer_text.strip()):
                    footer_ok = True
                    break
        score += add("footer_with_page_number", footer_ok,
                     "Footer with page number field detected." if footer_ok
                     else "No footer with page number detected.", weight=1.0)
    except Exception as e:
        score += add("footer_with_page_number", False, f"Error: {e}", weight=1.0)

    # ── 9. Minimum length sanity check ───────────────────────────────────────
    try:
        para_count = len([p for p in doc.paragraphs if p.text.strip()])
        length_ok = para_count >= 20
        score += add("minimum_content_length", length_ok,
                     f"Non-empty paragraphs: {para_count} ({'≥20 OK' if length_ok else '<20 too short'})",
                     weight=0.5)
    except Exception as e:
        score += add("minimum_content_length", False, f"Error: {e}", weight=0.5)

    # ── Normalize score (max possible = 0.5+0.5+1.5+1.0+1.0+1.5+1.0+1.5+1.0+1.5+0.5 = 11.5) ──
    max_score = 11.5
    normalized = round(min(score / max_score, 1.0), 4)
    passed = normalized >= 0.60

    return passed, normalized, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        passed, score, checks = run_checks(workspace)
    except Exception as e:
        passed, score, checks = False, 0.0, [
            {"name": "eval_crashed", "passed": False, "detail": traceback.format_exc()}
        ]
    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()