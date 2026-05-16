#!/usr/bin/env python3
"""
Evaluation script for the OFD digitization task.
Checks:
1. A .txt file was produced containing key text content from the OFD.
2. A .md file was produced containing Markdown table structure and headings.
3. Both files are non-trivially correct (not empty, not just echoed garbage).
"""
import sys
import json
import re
from pathlib import Path

def find_file_by_ext(workspace, ext):
    """Find files by extension, excluding distractor files."""
    workspace = Path(workspace)
    found = []
    for p in workspace.rglob(f"*{ext}"):
        # Exclude pre-existing distractor files
        rel = p.relative_to(workspace)
        parts = rel.parts
        # Skip files in incoming_documents (those are source, not output)
        if "incoming_documents" in parts:
            continue
        # Skip scripts folder
        if "scripts" in parts:
            continue
        # Must be a regular file
        if p.is_file():
            found.append(p)
    return found

def run_checks(workspace):
    checks = []
    workspace = Path(workspace)

    # ── CHECK 1: Text file exists ────────────────────────────────────────────
    txt_files = find_file_by_ext(workspace, ".txt")
    # Also check processed/text and root level
    txt_candidates = [f for f in txt_files if f.suffix == ".txt"]
    
    txt_found = len(txt_candidates) > 0
    checks.append({
        "name": "text_output_file_exists",
        "passed": txt_found,
        "detail": f"Found .txt output files: {[str(f) for f in txt_candidates]}" if txt_found else "No .txt output file found (excluding distractors and source folder)"
    })

    # ── CHECK 2: Text file contains key content ──────────────────────────────
    txt_content_ok = False
    txt_content_detail = "No valid .txt file to check"
    if txt_candidates:
        # Use the most recently produced one or iterate all
        for cand in txt_candidates:
            try:
                content = cand.read_text(encoding="utf-8", errors="replace")
                # Must contain the document title and some body text
                has_title = "2024年度政府采购公告" in content
                has_body = "采购" in content and "投标" in content
                has_items = "激光打印机" in content or "A001" in content
                if has_title and has_body and has_items:
                    txt_content_ok = True
                    txt_content_detail = f"File {cand}: contains title, body text, and procurement items"
                    break
                else:
                    txt_content_detail = (
                        f"File {cand}: has_title={has_title}, has_body={has_body}, has_items={has_items}. "
                        f"Content preview: {content[:300]!r}"
                    )
            except Exception as e:
                txt_content_detail = f"Error reading {cand}: {e}"

    checks.append({
        "name": "text_output_contains_correct_content",
        "passed": txt_content_ok,
        "detail": txt_content_detail
    })

    # ── CHECK 3: Markdown file exists ────────────────────────────────────────
    md_files = find_file_by_ext(workspace, ".md")
    md_found = len(md_files) > 0
    checks.append({
        "name": "markdown_output_file_exists",
        "passed": md_found,
        "detail": f"Found .md output files: {[str(f) for f in md_files]}" if md_found else "No .md output file found"
    })

    # ── CHECK 4: Markdown contains proper table syntax ───────────────────────
    md_table_ok = False
    md_table_detail = "No valid .md file to check"
    if md_files:
        for cand in md_files:
            try:
                content = cand.read_text(encoding="utf-8", errors="replace")
                # Markdown table: lines starting with | and containing ---
                table_lines = [l for l in content.splitlines() if l.strip().startswith("|")]
                separator_lines = [l for l in table_lines if "---" in l]
                has_table = len(table_lines) >= 3 and len(separator_lines) >= 1
                if has_table:
                    md_table_ok = True
                    md_table_detail = f"File {cand}: found Markdown table with {len(table_lines)} pipe-lines and {len(separator_lines)} separator lines"
                    break
                else:
                    md_table_detail = (
                        f"File {cand}: table_lines={len(table_lines)}, separator_lines={len(separator_lines)}. "
                        f"Content preview: {content[:400]!r}"
                    )
            except Exception as e:
                md_table_detail = f"Error reading {cand}: {e}"

    checks.append({
        "name": "markdown_contains_table_syntax",
        "passed": md_table_ok,
        "detail": md_table_detail
    })

    # ── CHECK 5: Markdown contains heading syntax (##) ───────────────────────
    md_heading_ok = False
    md_heading_detail = "No valid .md file to check"
    if md_files:
        for cand in md_files:
            try:
                content = cand.read_text(encoding="utf-8", errors="replace")
                heading_lines = [l for l in content.splitlines() if re.match(r"^#{1,6}\s+", l)]
                has_headings = len(heading_lines) >= 1
                # Should contain at least one of the chapter headings
                has_chapter = any("条" in l or "采购" in l for l in heading_lines)
                if has_headings and has_chapter:
                    md_heading_ok = True
                    md_heading_detail = f"File {cand}: found {len(heading_lines)} heading(s): {heading_lines[:3]}"
                    break
                else:
                    md_heading_detail = (
                        f"File {cand}: heading_lines={heading_lines}, has_chapter={has_chapter}"
                    )
            except Exception as e:
                md_heading_detail = f"Error reading {cand}: {e}"

    checks.append({
        "name": "markdown_contains_heading_syntax",
        "passed": md_heading_ok,
        "detail": md_heading_detail
    })

    # ── CHECK 6: Markdown contains procurement table data ────────────────────
    md_data_ok = False
    md_data_detail = "No valid .md file to check"
    if md_files:
        for cand in md_files:
            try:
                content = cand.read_text(encoding="utf-8", errors="replace")
                has_header_row = "品目名称" in content or "品目编号" in content
                has_data_row = "激光打印机" in content and "A001" in content
                has_price = "3500" in content or "28000" in content
                if has_header_row and has_data_row and has_price:
                    md_data_ok = True
                    md_data_detail = f"File {cand}: contains table headers, item data (A001, 激光打印机), and price data"
                    break
                else:
                    md_data_detail = (
                        f"File {cand}: has_header_row={has_header_row}, "
                        f"has_data_row={has_data_row}, has_price={has_price}"
                    )
            except Exception as e:
                md_data_detail = f"Error reading {cand}: {e}"

    checks.append({
        "name": "markdown_table_contains_procurement_data",
        "passed": md_data_ok,
        "detail": md_data_detail
    })

    # ── Scoring ──────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total
    all_passed = passed_count == total

    return {
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    workspace_dir = sys.argv[1]
    result = run_checks(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))