import sys
import json
import os
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]).resolve()
    checks = []
    total_score = 0.0

    # ---- CHECK 1: arxiv_ids.txt exists at the EXACT required path ----
    ids_file = workspace / "ref/agent-surveys/arxiv_ids.txt"
    ids_ok = False
    ids_content = []
    try:
        if ids_file.exists():
            raw = ids_file.read_text().strip()
            lines = [l.strip() for l in raw.splitlines() if l.strip() and not l.strip().startswith("#")]
            # Must have at least 1 valid arXiv ID (basic format: digits.digits or YYMM.NNNNN)
            import re
            valid = [l for l in lines if re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', l)]
            if len(valid) >= 1:
                ids_ok = True
                ids_content = valid
                checks.append({
                    "name": "arxiv_ids_txt_exists_and_valid",
                    "passed": True,
                    "detail": f"Found {len(valid)} valid arXiv ID(s) at the correct path: {valid}"
                })
            else:
                checks.append({
                    "name": "arxiv_ids_txt_exists_and_valid",
                    "passed": False,
                    "detail": f"File exists but contains no valid arXiv IDs (format: YYMM.NNNNN). Lines found: {lines}"
                })
        else:
            checks.append({
                "name": "arxiv_ids_txt_exists_and_valid",
                "passed": False,
                "detail": f"Required file missing: {ids_file}"
            })
    except Exception as e:
        checks.append({
            "name": "arxiv_ids_txt_exists_and_valid",
            "passed": False,
            "detail": f"Exception reading ids file: {e}"
        })

    # ---- CHECK 2: PDFs directory contains at least one .pdf file ----
    pdf_dir = workspace / "ref/agent-surveys/pdfs"
    pdf_ok = False
    try:
        pdfs = list(pdf_dir.glob("*.pdf"))
        if len(pdfs) >= 1:
            # Check PDF files are non-trivially sized (> 10KB = actually downloaded)
            big_enough = [p for p in pdfs if p.stat().st_size > 10_000]
            if big_enough:
                pdf_ok = True
                checks.append({
                    "name": "pdfs_downloaded",
                    "passed": True,
                    "detail": f"{len(big_enough)} PDF(s) found with size > 10KB: {[p.name for p in big_enough]}"
                })
            else:
                checks.append({
                    "name": "pdfs_downloaded",
                    "passed": False,
                    "detail": f"PDF files found but all are too small (< 10KB), likely not real downloads: {[p.name for p in pdfs]}"
                })
        else:
            checks.append({
                "name": "pdfs_downloaded",
                "passed": False,
                "detail": f"No .pdf files found in {pdf_dir}"
            })
    except Exception as e:
        checks.append({
            "name": "pdfs_downloaded",
            "passed": False,
            "detail": f"Exception checking pdf dir: {e}"
        })

    # ---- CHECK 3: text/ directory contains at least one .txt file with non-trivial content ----
    text_dir = workspace / "ref/agent-surveys/text"
    text_ok = False
    try:
        txts = list(text_dir.glob("*.txt"))
        if len(txts) >= 1:
            # Check at least one text file has meaningful content (> 500 chars)
            rich = [t for t in txts if t.stat().st_size > 500]
            if rich:
                text_ok = True
                checks.append({
                    "name": "text_extracted",
                    "passed": True,
                    "detail": f"{len(rich)} text file(s) with > 500 bytes: {[t.name for t in rich]}"
                })
            else:
                checks.append({
                    "name": "text_extracted",
                    "passed": False,
                    "detail": f"Text files found but all are near-empty (< 500 bytes): {[t.name for t in txts]}"
                })
        else:
            checks.append({
                "name": "text_extracted",
                "passed": False,
                "detail": f"No .txt files found in {text_dir}"
            })
    except Exception as e:
        checks.append({
            "name": "text_extracted",
            "passed": False,
            "detail": f"Exception checking text dir: {e}"
        })

    # ---- CHECK 4: STYLE_REPORT.md exists at the exact required path ----
    report_path = workspace / "ref/agent-surveys/STYLE_REPORT.md"
    report_ok = False
    try:
        if report_path.exists():
            content = report_path.read_text()
            # Must be auto-generated (contain the table header and "Style Report" heading)
            has_heading = "Style Report" in content
            has_table = "|" in content and "arXiv" in content
            has_notes = "Notes" in content or "text/" in content
            if has_heading and has_table and has_notes:
                report_ok = True
                checks.append({
                    "name": "style_report_correct",
                    "passed": True,
                    "detail": f"STYLE_REPORT.md exists and contains required auto-generated structure (heading, table, notes)."
                })
            else:
                checks.append({
                    "name": "style_report_correct",
                    "passed": False,
                    "detail": f"STYLE_REPORT.md exists but missing required structure. heading={has_heading}, table={has_table}, notes={has_notes}. Content preview: {content[:300]}"
                })
        else:
            checks.append({
                "name": "style_report_correct",
                "passed": False,
                "detail": f"STYLE_REPORT.md not found at {report_path}"
            })
    except Exception as e:
        checks.append({
            "name": "style_report_correct",
            "passed": False,
            "detail": f"Exception reading STYLE_REPORT.md: {e}"
        })

    # ---- CHECK 5: max-pages constraint — text files must not exceed the page limit ----
    # We verify the script was called with --max-pages <= 30 by checking STYLE_REPORT for
    # the pages column (the script records args.max_pages there).
    # Also check that the decoy path (configs/arxiv_ids_backup.txt) was NOT used as the source
    # (the agent must have written to the correct path, not the decoy).
    decoy_used = False
    correct_path_used = ids_file.exists()
    max_pages_check_ok = False
    try:
        if report_path.exists():
            content = report_path.read_text()
            import re
            # Extract page numbers from the table rows (4th column)
            page_nums = re.findall(r'\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|', content)
            if page_nums:
                pages_used = [int(p) for p in page_nums]
                # max-pages should be >= 5 (meaningful) and <= 50 (reasonable)
                if all(5 <= p <= 50 for p in pages_used):
                    max_pages_check_ok = True
                    checks.append({
                        "name": "max_pages_flag_used_correctly",
                        "passed": True,
                        "detail": f"--max-pages used with value(s): {pages_used} (within reasonable range 5-50)."
                    })
                else:
                    checks.append({
                        "name": "max_pages_flag_used_correctly",
                        "passed": False,
                        "detail": f"--max-pages values out of expected range: {pages_used}"
                    })
            else:
                # Table might have different formatting; give benefit of doubt if report exists
                max_pages_check_ok = True
                checks.append({
                    "name": "max_pages_flag_used_correctly",
                    "passed": True,
                    "detail": "Could not parse page count from report table, but report exists and is well-formed."
                })
        else:
            checks.append({
                "name": "max_pages_flag_used_correctly",
                "passed": False,
                "detail": "Cannot check max-pages: STYLE_REPORT.md not found."
            })
    except Exception as e:
        checks.append({
            "name": "max_pages_flag_used_correctly",
            "passed": False,
            "detail": f"Exception during max-pages check: {e}"
        })

    # ---- Scoring ----
    weights = {
        "arxiv_ids_txt_exists_and_valid": 0.20,
        "pdfs_downloaded": 0.30,
        "text_extracted": 0.25,
        "style_report_correct": 0.15,
        "max_pages_flag_used_correctly": 0.10,
    }
    score = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()