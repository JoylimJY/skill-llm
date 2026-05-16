import sys
import json
import traceback
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    overall_passed = True

    # ── Check 1: Output file exists ──────────────────────────────────────────
    try:
        candidates = list(Path(workspace).rglob("compound_abc201_brief.docx"))
        if not candidates:
            checks.append({
                "name": "output_file_exists",
                "passed": False,
                "detail": "No file named 'compound_abc201_brief.docx' found anywhere in workspace."
            })
            overall_passed = False
            return checks, overall_passed
        output_path = candidates[0]
        checks.append({
            "name": "output_file_exists",
            "passed": True,
            "detail": f"Found output file at: {output_path}"
        })
    except Exception as e:
        checks.append({"name": "output_file_exists", "passed": False, "detail": str(e)})
        overall_passed = False
        return checks, overall_passed

    # ── Load the docx ────────────────────────────────────────────────────────
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.oxml.ns import qn
        doc = Document(str(output_path))
    except Exception as e:
        checks.append({"name": "docx_loadable", "passed": False, "detail": f"Failed to open docx: {e}"})
        overall_passed = False
        return checks, overall_passed

    checks.append({"name": "docx_loadable", "passed": True, "detail": "DOCX loaded successfully."})

    # ── Check 2: H1 heading formatting (18pt, 微软雅黑, bold) ─────────────────
    try:
        h1_found = False
        for para in doc.paragraphs:
            for run in para.runs:
                if "Compound ABC-201 Clinical Research Brief" in run.text:
                    size_ok = run.font.size is not None and abs(run.font.size.pt - 18) < 0.5
                    bold_ok = run.bold is True
                    font_name = run.font.name or ""
                    font_ok = "雅黑" in font_name or "YaHei" in font_name
                    # Check east asia font via XML
                    if not font_ok:
                        rpr = run._element.find(qn("w:rPr"))
                        if rpr is not None:
                            rfonts = rpr.find(qn("w:rFonts"))
                            if rfonts is not None:
                                ea = rfonts.get(qn("w:eastAsia"), "")
                                font_ok = "雅黑" in ea or "YaHei" in ea
                    if size_ok and bold_ok:
                        h1_found = True
                        checks.append({
                            "name": "h1_formatting_18pt_bold_yahei",
                            "passed": True,
                            "detail": f"H1 run found: size={run.font.size.pt}pt, bold={run.bold}, font='{run.font.name}', eastAsia font check={font_ok}"
                        })
                        break
            if h1_found:
                break
        if not h1_found:
            checks.append({
                "name": "h1_formatting_18pt_bold_yahei",
                "passed": False,
                "detail": "Could not find H1 run with 18pt bold formatting for 'Compound ABC-201 Clinical Research Brief'."
            })
            overall_passed = False
    except Exception as e:
        checks.append({"name": "h1_formatting_18pt_bold_yahei", "passed": False, "detail": traceback.format_exc()})
        overall_passed = False

    # ── Check 3: H2 heading at 14pt ──────────────────────────────────────────
    try:
        h2_found = False
        for para in doc.paragraphs:
            for run in para.runs:
                if "Executive Summary" in run.text:
                    size_ok = run.font.size is not None and abs(run.font.size.pt - 14) < 0.5
                    bold_ok = run.bold is True
                    if size_ok and bold_ok:
                        h2_found = True
                        checks.append({
                            "name": "h2_formatting_14pt_bold",
                            "passed": True,
                            "detail": f"H2 'Executive Summary' at {run.font.size.pt}pt bold."
                        })
                        break
            if h2_found:
                break
        if not h2_found:
            checks.append({
                "name": "h2_formatting_14pt_bold",
                "passed": False,
                "detail": "H2 'Executive Summary' not found at 14pt bold."
            })
            overall_passed = False
    except Exception as e:
        checks.append({"name": "h2_formatting_14pt_bold", "passed": False, "detail": traceback.format_exc()})
        overall_passed = False

    # ── Check 4: H3 heading at 12pt ──────────────────────────────────────────
    try:
        h3_found = False
        for para in doc.paragraphs:
            for run in para.runs:
                if "Pharmacokinetics" in run.text:
                    size_ok = run.font.size is not None and abs(run.font.size.pt - 12) < 0.5
                    bold_ok = run.bold is True
                    if size_ok and bold_ok:
                        h3_found = True
                        checks.append({
                            "name": "h3_formatting_12pt_bold",
                            "passed": True,
                            "detail": f"H3 'Pharmacokinetics' at {run.font.size.pt}pt bold."
                        })
                        break
            if h3_found:
                break
        if not h3_found:
            checks.append({
                "name": "h3_formatting_12pt_bold",
                "passed": False,
                "detail": "H3 'Pharmacokinetics' not found at 12pt bold."
            })
            overall_passed = False
    except Exception as e:
        checks.append({"name": "h3_formatting_12pt_bold", "passed": False, "detail": traceback.format_exc()})
        overall_passed = False

    # ── Check 5: Table exists with correct data ───────────────────────────────
    try:
        table_found = False
        table_has_abc201 = False
        table_header_blue = False

        for table in doc.tables:
            for row_idx, row in enumerate(table.rows):
                row_text = [cell.text.strip() for cell in row.cells]
                if "ABC-201" in row_text or any("4.2" in t for t in row_text):
                    table_found = True
                    table_has_abc201 = True
                if row_idx == 0:
                    # Check blue background on first row cells
                    for cell in row.cells:
                        tc = cell._tc
                        tcPr = tc.find(qn("w:tcPr"))
                        if tcPr is not None:
                            shd = tcPr.find(qn("w:shd"))
                            if shd is not None:
                                fill = shd.get(qn("w:fill"), "").upper()
                                if fill in ("2E74B5", "2E74B5".upper(), "2e74b5".upper()):
                                    table_header_blue = True
                                    break

        if table_found and table_has_abc201:
            checks.append({
                "name": "table_data_present",
                "passed": True,
                "detail": "Table with ABC-201 compound data found in document."
            })
        else:
            checks.append({
                "name": "table_data_present",
                "passed": False,
                "detail": "Table with ABC-201 data not found."
            })
            overall_passed = False

        if table_header_blue:
            checks.append({
                "name": "table_header_blue_background",
                "passed": True,
                "detail": "Table header row has blue background (2E74B5) — proprietary formatting confirmed."
            })
        else:
            checks.append({
                "name": "table_header_blue_background",
                "passed": False,
                "detail": "Table header row does NOT have the proprietary blue background (2E74B5). A generic converter was likely used."
            })
            overall_passed = False

    except Exception as e:
        checks.append({"name": "table_checks", "passed": False, "detail": traceback.format_exc()})
        overall_passed = False

    # ── Check 6: Blockquote rendered as italic indented text ─────────────────
    try:
        blockquote_italic = False
        for para in doc.paragraphs:
            if "All data presented herein" in para.text:
                for run in para.runs:
                    if run.italic and para.paragraph_format.left_indent is not None:
                        blockquote_italic = True
                        break
        if blockquote_italic:
            checks.append({
                "name": "blockquote_italic_indented",
                "passed": True,
                "detail": "Blockquote text is italic and indented."
            })
        else:
            checks.append({
                "name": "blockquote_italic_indented",
                "passed": False,
                "detail": "Blockquote text ('All data presented herein...') not found as italic/indented paragraph."
            })
            overall_passed = False
    except Exception as e:
        checks.append({"name": "blockquote_italic_indented", "passed": False, "detail": traceback.format_exc()})
        overall_passed = False

    # ── Check 7: Bullet list items present ───────────────────────────────────
    try:
        bullet_found = False
        for para in doc.paragraphs:
            if para.style and "List Bullet" in para.style.name:
                if "Half-life" in para.text or "Bioavailability" in para.text:
                    bullet_found = True
                    break
        if bullet_found:
            checks.append({
                "name": "bullet_list_present",
                "passed": True,
                "detail": "Bullet list items found in document with 'List Bullet' style."
            })
        else:
            checks.append({
                "name": "bullet_list_present",
                "passed": False,
                "detail": "No 'List Bullet' styled paragraphs with expected content found."
            })
            overall_passed = False
    except Exception as e:
        checks.append({"name": "bullet_list_present", "passed": False, "detail": traceback.format_exc()})
        overall_passed = False

    # ── Check 8: Numbered list items present ─────────────────────────────────
    try:
        numbered_found = False
        for para in doc.paragraphs:
            if para.style and "List Number" in para.style.name:
                numbered_found = True
                break
        if numbered_found:
            checks.append({
                "name": "numbered_list_present",
                "passed": True,
                "detail": "Numbered list items found in document with 'List Number' style."
            })
        else:
            checks.append({
                "name": "numbered_list_present",
                "passed": False,
                "detail": "No 'List Number' styled paragraphs found."
            })
            overall_passed = False
    except Exception as e:
        checks.append({"name": "numbered_list_present", "passed": False, "detail": traceback.format_exc()})
        overall_passed = False

    return checks, overall_passed


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, overall_passed = run_checks(workspace)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / len(checks) if checks else 0.0
    result = {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()