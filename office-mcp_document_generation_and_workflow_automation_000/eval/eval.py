import sys
import json
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    workspace = Path(workspace)

    # ── HELPER ──────────────────────────────────────────────────────────────
    def add(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ════════════════════════════════════════════════════════════════════════
    # 1.  EXCEL CHECK  (q3_sales_report.xlsx)
    # ════════════════════════════════════════════════════════════════════════
    xlsx_files = list(workspace.rglob("q3_sales_report.xlsx"))
    if not xlsx_files:
        add("xlsx_file_exists", False, "q3_sales_report.xlsx not found anywhere in workspace")
    else:
        xlsx_path = xlsx_files[0]
        add("xlsx_file_exists", True, f"Found at {xlsx_path}")

        try:
            from openpyxl import load_workbook
            wb = load_workbook(xlsx_path)
            ws = wb.active

            all_rows = list(ws.iter_rows(values_only=True))

            # Check header row
            header = [str(c).strip() if c is not None else "" for c in all_rows[0]]
            expected_header = ["Store", "Product", "Month", "Units Sold", "Unit Price", "Total Revenue"]
            header_ok = all(e.lower() in h.lower() for e, h in zip(expected_header, header))
            add("xlsx_header_correct", header_ok,
                f"Header row: {header}")

            # Check no blank rows in data section (all data rows must have a non-empty Store)
            data_rows = all_rows[1:]  # skip header
            # last row may be TOTALS — be lenient about that
            non_totals = [r for r in data_rows if r[0] is not None and str(r[0]).strip().upper() != "TOTALS"]
            blank_in_data = any(
                all(c is None or str(c).strip() == "" for c in row)
                for row in non_totals
            )
            add("xlsx_no_blank_rows", not blank_in_data,
                "No blank rows found in data section" if not blank_in_data
                else "Blank rows still present in Excel data")

            # Check trailing whitespace stripped from store names
            store_names = [str(r[0]).strip() for r in non_totals if r[0] is not None]
            trailing_ws = any(s != s.strip() for s in [str(r[0]) for r in non_totals if r[0] is not None])
            add("xlsx_store_names_stripped", not trailing_ws,
                "Store names have no trailing whitespace" if not trailing_ws
                else "Some store names still have trailing whitespace")

            # Check TOTALS row exists
            last_row = all_rows[-1]
            totals_row_exists = last_row[0] is not None and "TOTAL" in str(last_row[0]).upper()
            add("xlsx_totals_row_exists", totals_row_exists,
                f"Last row: {last_row}")

            # Check TOTALS row has numeric sums for Units Sold (col 4) and Revenue (col 6)
            if totals_row_exists:
                try:
                    units_total = float(last_row[3])
                    rev_total   = float(last_row[5])
                    # Compute expected sums from non-blank data rows (excluding header and totals)
                    data_only = [r for r in all_rows[1:-1]
                                 if r[0] is not None and str(r[0]).strip() != ""
                                 and str(r[0]).strip().upper() != "TOTALS"]
                    expected_units = sum(float(r[3]) for r in data_only if r[3] is not None)
                    expected_rev   = sum(float(r[5]) for r in data_only if r[5] is not None)
                    sums_ok = (abs(units_total - expected_units) < 1 and
                               abs(rev_total - expected_rev) < 1)
                    add("xlsx_totals_sums_correct", sums_ok,
                        f"Units total {units_total} vs expected {expected_units:.0f}; "
                        f"Revenue total {rev_total:.2f} vs expected {expected_rev:.2f}")
                except Exception as e:
                    add("xlsx_totals_sums_correct", False, f"Error reading totals: {e}")
            else:
                add("xlsx_totals_sums_correct", False, "Totals row not found, cannot verify sums")

        except Exception as e:
            add("xlsx_content_check", False, f"Failed to open/parse xlsx: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # 2.  WORD CHECK  (q3_executive_summary.docx)
    # ════════════════════════════════════════════════════════════════════════
    docx_files = list(workspace.rglob("q3_executive_summary.docx"))
    if not docx_files:
        add("docx_file_exists", False, "q3_executive_summary.docx not found anywhere in workspace")
    else:
        docx_path = docx_files[0]
        add("docx_file_exists", True, f"Found at {docx_path}")

        try:
            from docx import Document
            doc = Document(str(docx_path))

            paragraphs = [p for p in doc.paragraphs if p.text.strip()]

            # Check title heading (level 0 = 'Title' style OR style name contains 'Title' or heading level 0)
            title_para = paragraphs[0] if paragraphs else None
            if title_para:
                title_text = title_para.text.strip()
                title_content_ok = "Q3 2024" in title_text and "Summary" in title_text
                add("docx_title_content", title_content_ok,
                    f"Title paragraph text: '{title_text}'")

                # The SKILL.md mandates add_heading(title, 0) — style should be 'Title' or heading 0
                style_name = title_para.style.name if title_para.style else ""
                title_style_ok = ("Title" in style_name or
                                  "Heading" in style_name or
                                  style_name.lower() in ("title", "heading 1", "heading 2"))
                add("docx_title_is_heading_style", title_style_ok,
                    f"Title paragraph style: '{style_name}' (expected heading/Title style from add_heading call)")
            else:
                add("docx_title_content", False, "No paragraphs found in docx")
                add("docx_title_is_heading_style", False, "No paragraphs found")

            # Check body paragraph mentions key business content
            full_text = " ".join(p.text for p in paragraphs).lower()
            has_transactions = any(w in full_text for w in ["transaction", "record", "row", "sale", "data point"])
            has_store = any(s.lower() in full_text for s in ["downtown", "westside", "northgate", "eastpark", "southmall"])
            has_revenue = "revenue" in full_text or "$" in full_text or "total" in full_text

            add("docx_body_mentions_transactions", has_transactions,
                f"Body mentions transaction count: {has_transactions}")
            add("docx_body_mentions_top_store", has_store,
                f"Body mentions a store name: {has_store}")
            add("docx_body_mentions_revenue", has_revenue,
                f"Body mentions revenue: {has_revenue}")

        except Exception as e:
            add("docx_content_check", False, f"Failed to open/parse docx: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # 3.  POWERPOINT CHECK  (q3_board_deck.pptx)
    # ════════════════════════════════════════════════════════════════════════
    pptx_files = list(workspace.rglob("q3_board_deck.pptx"))
    if not pptx_files:
        add("pptx_file_exists", False, "q3_board_deck.pptx not found anywhere in workspace")
    else:
        pptx_path = pptx_files[0]
        add("pptx_file_exists", True, f"Found at {pptx_path}")

        try:
            from pptx import Presentation

            prs = Presentation(str(pptx_path))
            slides = prs.slides
            slide_count = len(slides)

            add("pptx_at_least_3_slides", slide_count >= 3,
                f"Slide count: {slide_count}")

            def slide_text(slide):
                texts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        texts.append(shape.text.strip())
                return " ".join(texts)

            # Slide 1: should contain "Q3 2024 Board Review" or similar
            s1_text = slide_text(slides[0]).lower()
            s1_ok = "q3" in s1_text and ("board" in s1_text or "review" in s1_text or "2024" in s1_text)
            add("pptx_slide1_title_content", s1_ok,
                f"Slide 1 text: '{slide_text(slides[0])[:120]}'")

            # Slide 2: should contain "Performance" or "Highlights" and store names
            s2_text = slide_text(slides[1]).lower()
            s2_has_header = "performance" in s2_text or "highlight" in s2_text
            s2_has_stores = sum(
                1 for s in ["downtown", "westside", "northgate", "eastpark", "southmall"]
                if s in s2_text
            )
            add("pptx_slide2_performance_header", s2_has_header,
                f"Slide 2 text: '{slide_text(slides[1])[:120]}'")
            add("pptx_slide2_has_store_names", s2_has_stores >= 2,
                f"Slide 2 mentions {s2_has_stores} store names (need >=2 for top 3)")

            # Slide 3: should contain "Next Steps" or "Recommendation"
            s3_text = slide_text(slides[2]).lower()
            s3_ok = "next" in s3_text or "step" in s3_text or "recommend" in s3_text or "action" in s3_text
            add("pptx_slide3_next_steps", s3_ok,
                f"Slide 3 text: '{slide_text(slides[2])[:120]}'")

        except Exception as e:
            add("pptx_content_check", False, f"Failed to open/parse pptx: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # 4.  PLACEMENT CHECK – all three files in reports/final/
    # ════════════════════════════════════════════════════════════════════════
    final_dir = workspace / "reports" / "final"
    files_in_final = list(final_dir.glob("*")) if final_dir.exists() else []
    target_names = {"q3_sales_report.xlsx", "q3_executive_summary.docx", "q3_board_deck.pptx"}
    found_names   = {f.name for f in files_in_final}
    placed_ok     = target_names.issubset(found_names)
    add("all_files_in_reports_final", placed_ok,
        f"Files found in reports/final: {sorted(found_names)}")

    # ════════════════════════════════════════════════════════════════════════
    # SCORE
    # ════════════════════════════════════════════════════════════════════════
    passed_count = sum(1 for c in checks if c["passed"])
    total        = len(checks)
    score        = round(passed_count / total, 4) if total else 0.0
    overall      = passed_count == total

    return {"passed": overall, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2))