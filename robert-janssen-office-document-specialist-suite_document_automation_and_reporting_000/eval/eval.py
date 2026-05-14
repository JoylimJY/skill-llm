import sys
import json
import traceback
from pathlib import Path
from collections import defaultdict

def make_result(checks):
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 4) if checks else 0.0
    overall = all(c["passed"] for c in checks)
    return {"passed": overall, "score": score, "checks": checks}

def find_unique(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    if not matches:
        return None
    return matches[0]

def compute_expected(workspace):
    """Re-derive expected aggregates from the original input file."""
    import openpyxl
    wb = openpyxl.load_workbook(Path(workspace) / "raw_data" / "q1_2024_sales_export.xlsx")
    ws = wb["Q1_Sales"]

    region_units = defaultdict(int)
    region_revenue = defaultdict(float)
    region_returns = defaultdict(int)

    # Data rows start at row 5 (1-indexed), headers at row 3, spacer at 4
    # Rows 5..24 are data; row 25 is NOTE, 26 blank, 27 TOTALS — skip all non-data
    for row in ws.iter_rows(min_row=5, max_row=ws.max_row, values_only=True):
        if row[0] is None:
            continue
        val = str(row[0]).strip().upper()
        if val in ("NOTE:", "TOTALS", "") or row[0] is None:
            continue
        if str(row[0]).strip().upper().startswith("NOTE"):
            continue
        if str(row[0]).strip().upper() == "TOTALS":
            continue
        try:
            region = str(row[0]).strip().capitalize()
            units = int(row[3]) if row[3] is not None else 0
            price = float(row[4]) if row[4] is not None else 0.0
            returns = int(row[5]) if row[5] is not None else 0
            region_units[region] += units
            region_revenue[region] += units * price
            region_returns[region] += returns
        except (TypeError, ValueError):
            continue

    return region_units, region_revenue, region_returns

def check_word_report(workspace, region_units, region_revenue, region_returns):
    checks = []
    try:
        from docx import Document
        from docx.oxml.ns import qn
    except ImportError:
        checks.append({"name": "word_import", "passed": False, "detail": "python-docx not available"})
        return checks

    docx_path = find_unique(workspace, "quarterly_sales_report.docx")
    if docx_path is None:
        checks.append({"name": "word_file_exists", "passed": False, "detail": "quarterly_sales_report.docx not found anywhere in workspace"})
        return checks
    checks.append({"name": "word_file_exists", "passed": True, "detail": str(docx_path)})

    try:
        doc = Document(str(docx_path))
    except Exception as e:
        checks.append({"name": "word_file_parseable", "passed": False, "detail": str(e)})
        return checks
    checks.append({"name": "word_file_parseable", "passed": True, "detail": "Document opened without error"})

    # Check: document has at least one Heading 1 style paragraph
    headings = [p for p in doc.paragraphs if p.style.name.startswith("Heading")]
    has_heading = len(headings) >= 1
    checks.append({
        "name": "word_has_heading",
        "passed": has_heading,
        "detail": f"Found {len(headings)} heading paragraph(s). Expected >= 1."
    })

    # Check: document contains a table
    has_table = len(doc.tables) >= 1
    checks.append({
        "name": "word_has_table",
        "passed": has_table,
        "detail": f"Found {len(doc.tables)} table(s). Expected >= 1."
    })

    if not has_table:
        return checks

    # Check: the table contains the 4 regions (case-insensitive)
    expected_regions = {"north", "south", "east", "west"}
    found_regions = set()
    all_cell_text = []
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                txt = cell.text.strip().lower()
                all_cell_text.append(txt)
                for r in expected_regions:
                    if r in txt:
                        found_regions.add(r)

    regions_present = expected_regions.issubset(found_regions)
    checks.append({
        "name": "word_table_has_all_regions",
        "passed": regions_present,
        "detail": f"Found regions in table: {found_regions}. Expected: {expected_regions}"
    })

    # Check: document body text contains "Q1 2024" or "Q1" somewhere (as a mention of the quarter)
    all_text = " ".join(p.text for p in doc.paragraphs).lower()
    has_quarter_mention = "q1" in all_text or "quarter" in all_text or "2024" in all_text
    checks.append({
        "name": "word_mentions_quarter",
        "passed": has_quarter_mention,
        "detail": f"Document body mentions Q1/quarter/2024: {has_quarter_mention}"
    })

    # Check: at least one numeric value in the table matches expected aggregated units (within rounding)
    expected_total_units = sum(region_units.values())
    numeric_found = False
    for txt in all_cell_text:
        try:
            val = float(txt.replace(",", ""))
            if abs(val - expected_total_units) < 5:
                numeric_found = True
                break
        except ValueError:
            pass
    # Also check per-region units
    if not numeric_found:
        for region, exp_units in region_units.items():
            for txt in all_cell_text:
                try:
                    val = float(txt.replace(",", ""))
                    if abs(val - exp_units) < 2:
                        numeric_found = True
                        break
                except ValueError:
                    pass
            if numeric_found:
                break

    checks.append({
        "name": "word_table_has_correct_aggregated_data",
        "passed": numeric_found,
        "detail": f"Expected total units ~{expected_total_units} or per-region units. Found matching value: {numeric_found}"
    })

    return checks


def check_powerpoint(workspace, region_units, region_revenue, region_returns):
    checks = []
    try:
        from pptx import Presentation
        from pptx.util import Inches
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError:
        checks.append({"name": "pptx_import", "passed": False, "detail": "python-pptx not available"})
        return checks

    pptx_path = find_unique(workspace, "q1_2024_executive_deck.pptx")
    if pptx_path is None:
        checks.append({"name": "pptx_file_exists", "passed": False, "detail": "q1_2024_executive_deck.pptx not found anywhere in workspace"})
        return checks
    checks.append({"name": "pptx_file_exists", "passed": True, "detail": str(pptx_path)})

    try:
        prs = Presentation(str(pptx_path))
    except Exception as e:
        checks.append({"name": "pptx_file_parseable", "passed": False, "detail": str(e)})
        return checks
    checks.append({"name": "pptx_file_parseable", "passed": True, "detail": "Presentation opened without error"})

    # Check: at least 3 slides
    slide_count = len(prs.slides)
    has_3_slides = slide_count >= 3
    checks.append({
        "name": "pptx_has_3_slides",
        "passed": has_3_slides,
        "detail": f"Found {slide_count} slide(s). Expected >= 3."
    })

    # Collect all text from all slides
    all_slide_text = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    all_slide_text.append(para.text.strip().lower())

    full_text = " ".join(all_slide_text)

    # Check: slide deck mentions the company or Q1 2024
    has_context = any(kw in full_text for kw in ["q1", "2024", "acme", "sales", "quarter"])
    checks.append({
        "name": "pptx_has_context_text",
        "passed": has_context,
        "detail": f"Deck text mentions Q1/2024/acme/sales/quarter: {has_context}"
    })

    # Check: deck contains at least one table shape
    table_found = False
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_table:
                table_found = True
                break
        if table_found:
            break

    checks.append({
        "name": "pptx_has_table_shape",
        "passed": table_found,
        "detail": f"At least one slide contains a table shape: {table_found}"
    })

    # Check: all 4 regions appear somewhere in the deck (text or table)
    expected_regions = {"north", "south", "east", "west"}
    found_regions = set()

    # From text frames
    for txt in all_slide_text:
        for r in expected_regions:
            if r in txt:
                found_regions.add(r)

    # From table cells
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        txt = cell.text.strip().lower()
                        for r in expected_regions:
                            if r in txt:
                                found_regions.add(r)

    regions_in_deck = expected_regions.issubset(found_regions)
    checks.append({
        "name": "pptx_has_all_regions",
        "passed": regions_in_deck,
        "detail": f"Regions found in deck: {found_regions}. Expected: {expected_regions}"
    })

    # Check: numeric aggregated data present (units or revenue totals)
    expected_total_units = sum(region_units.values())
    numeric_correct = False
    # Check tables
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        try:
                            val = float(cell.text.strip().replace(",", ""))
                            if abs(val - expected_total_units) < 5:
                                numeric_correct = True
                        except ValueError:
                            pass
    # Check text frames
    if not numeric_correct:
        for region, exp_units in region_units.items():
            for txt in all_slide_text:
                try:
                    val = float(txt.replace(",", ""))
                    if abs(val - exp_units) < 2:
                        numeric_correct = True
                        break
                except ValueError:
                    pass

    checks.append({
        "name": "pptx_has_correct_numeric_data",
        "passed": numeric_correct,
        "detail": f"Expected total units ~{expected_total_units} or per-region units in deck. Found: {numeric_correct}"
    })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    all_checks = []

    try:
        region_units, region_revenue, region_returns = compute_expected(workspace)
    except Exception as e:
        all_checks.append({"name": "input_data_readable", "passed": False, "detail": f"Could not read input Excel: {e}\n{traceback.format_exc()}"})
        print(json.dumps(make_result(all_checks)))
        return

    all_checks.append({"name": "input_data_readable", "passed": True, "detail": f"Regions: {dict(region_units)}"})

    # Evaluate Word report
    word_checks = check_word_report(workspace, region_units, region_revenue, region_returns)
    all_checks.extend(word_checks)

    # Evaluate PowerPoint deck
    pptx_checks = check_powerpoint(workspace, region_units, region_revenue, region_returns)
    all_checks.extend(pptx_checks)

    print(json.dumps(make_result(all_checks), indent=2))


if __name__ == "__main__":
    main()