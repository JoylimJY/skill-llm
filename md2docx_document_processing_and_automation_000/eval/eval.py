import sys
import json
import traceback
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # ---- Check 1: Find the output .docx file ----
    # The prompt asks to produce "product_spec_v3.2.docx"
    target_name = "product_spec_v3.2.docx"
    found_files = list(workspace.rglob(target_name))

    check_exists = {
        "name": "Output .docx file exists",
        "passed": False,
        "detail": f"No file named '{target_name}' found under workspace."
    }

    if found_files:
        check_exists["passed"] = True
        check_exists["detail"] = f"Found at: {found_files[0]}"
    
    checks.append(check_exists)

    if not found_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    docx_path = found_files[0]

    # ---- Check 2: File is a valid .docx (can be opened by python-docx) ----
    check_valid_docx = {
        "name": "File is a valid Word document",
        "passed": False,
        "detail": ""
    }
    document = None
    try:
        from docx import Document
        document = Document(str(docx_path))
        check_valid_docx["passed"] = True
        check_valid_docx["detail"] = "Successfully opened as a Word document."
    except Exception as e:
        check_valid_docx["detail"] = f"Failed to open as Word document: {e}"
    checks.append(check_valid_docx)

    if document is None:
        return {"passed": False, "score": round(1/4, 4), "checks": checks}

    # ---- Check 3: Document has meaningful content (headings/paragraphs from the spec) ----
    check_content = {
        "name": "Document contains expected content from spec Markdown",
        "passed": False,
        "detail": ""
    }
    try:
        all_text = "\n".join(p.text for p in document.paragraphs)
        # Check for some expected Chinese content and key terms
        required_snippets = [
            "智能仓储管理系统",
            "IWMS",
            "PostgreSQL",
        ]
        missing = [s for s in required_snippets if s not in all_text]
        if not missing:
            check_content["passed"] = True
            check_content["detail"] = "All required content snippets found."
        else:
            check_content["detail"] = f"Missing content snippets: {missing}"
    except Exception as e:
        check_content["detail"] = f"Error reading paragraphs: {e}"
    checks.append(check_content)

    # ---- Check 4: Tables exist (the Markdown has 3 tables) ----
    check_tables = {
        "name": "Document contains tables",
        "passed": False,
        "detail": ""
    }
    try:
        table_count = len(document.tables)
        if table_count >= 2:
            check_tables["passed"] = True
            check_tables["detail"] = f"Found {table_count} table(s)."
        else:
            check_tables["detail"] = f"Expected at least 2 tables, found {table_count}."
    except Exception as e:
        check_tables["detail"] = f"Error counting tables: {e}"
    checks.append(check_tables)

    # ---- Check 5 (PROPRIETARY): Tables have border XML elements set ----
    # This is only applied by the bespoke post-processing in tools/md2docx.py
    check_borders = {
        "name": "[PROPRIETARY] Tables have cell borders set (post-processing applied)",
        "passed": False,
        "detail": ""
    }
    try:
        from docx.oxml.ns import qn
        border_found = False
        border_details = []

        for table_idx, table in enumerate(document.tables):
            for row_idx, row in enumerate(table.rows):
                for cell_idx, cell in enumerate(row.cells):
                    tc = cell._tc
                    tcPr = tc.find(qn("w:tcPr"))
                    if tcPr is not None:
                        tcBorders = tcPr.find(qn("w:tcBorders"))
                        if tcBorders is not None:
                            # Check that at least one side is "single"
                            for side in ["w:top", "w:bottom", "w:left", "w:right"]:
                                el = tcBorders.find(qn(side))
                                if el is not None:
                                    val = el.get(qn("w:val"))
                                    if val == "single":
                                        border_found = True
                                        border_details.append(
                                            f"Table {table_idx}, Row {row_idx}, Cell {cell_idx}: {side}=single"
                                        )
                                        break
                    if border_found:
                        break
                if border_found:
                    break
            if border_found:
                break

        if border_found:
            check_borders["passed"] = True
            check_borders["detail"] = f"Border XML found: {border_details[0] if border_details else 'yes'}"
        else:
            check_borders["detail"] = (
                "No 'w:tcBorders' with val='single' found in any table cell. "
                "This indicates the proprietary post-processing step from tools/md2docx.py was NOT applied. "
                "A raw pandoc call without the two-stage pipeline will fail this check."
            )
    except Exception as e:
        check_borders["detail"] = f"Error inspecting table XML: {e}\n{traceback.format_exc()}"
    checks.append(check_borders)

    # ---- Check 6 (PROPRIETARY): Runs have Chinese fonts set ----
    # tools/md2docx.py sets run.font.name = "Microsoft YaHei" and eastAsia = "SimSun"
    check_fonts = {
        "name": "[PROPRIETARY] Chinese fonts set on paragraph runs (post-processing applied)",
        "passed": False,
        "detail": ""
    }
    try:
        from docx.oxml.ns import qn
        font_found = False
        font_detail = ""

        for para in document.paragraphs:
            for run in para.runs:
                # Check run.font.name (ascii font)
                if run.font.name in ("Microsoft YaHei",):
                    font_found = True
                    font_detail = f"Run font.name = '{run.font.name}' in paragraph: '{para.text[:40]}'"
                    break
                # Also check via XML rFonts eastAsia
                rPr = run._r.find(qn("w:rPr"))
                if rPr is not None:
                    rFonts = rPr.find(qn("w:rFonts"))
                    if rFonts is not None:
                        ea = rFonts.get(qn("w:eastAsia"))
                        ascii_font = rFonts.get(qn("w:ascii"))
                        if ea in ("SimSun", "Microsoft YaHei") or ascii_font in ("Microsoft YaHei",):
                            font_found = True
                            font_detail = f"rFonts eastAsia='{ea}' ascii='{ascii_font}' in para: '{para.text[:40]}'"
                            break
            if font_found:
                break

        if font_found:
            check_fonts["passed"] = True
            check_fonts["detail"] = font_detail
        else:
            check_fonts["detail"] = (
                "No 'Microsoft YaHei' or 'SimSun' font found on any run. "
                "This indicates the proprietary Chinese font post-processing step from tools/md2docx.py was NOT applied."
            )
    except Exception as e:
        check_fonts["detail"] = f"Error inspecting font XML: {e}\n{traceback.format_exc()}"
    checks.append(check_fonts)

    # ---- Compute final score ----
    # Weights: existence(1) + valid(1) + content(1) + tables(1) + borders(2) + fonts(2) = 8 points
    weights = [1, 1, 1, 1, 2, 2]
    total_weight = sum(weights)
    earned = sum(w for w, c in zip(weights, checks) if c["passed"])
    score = round(earned / total_weight, 4)

    # Must pass both proprietary checks to fully pass
    proprietary_passed = checks[4]["passed"] and checks[5]["passed"]
    basic_passed = all(c["passed"] for c in checks[:4])
    overall_passed = basic_passed and proprietary_passed

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [], "error": "No workspace path provided"}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))