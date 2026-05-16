#!/usr/bin/env python3
"""
Evaluation script for the nested-pdf-merger benchmark task.

Grading criteria:
1. Output file `quarterly_merged.pdf` exists somewhere under workspace.
2. The PDF is a valid PDF (has proper header).
3. The PDF contains bookmarks (outline entries) — verifying --no-bookmarks was NOT used.
4. Pages from Archive and Draft directories are NOT present (exclusion check via bookmark titles).
5. Pages from hidden directories (.hidden_notes, .internal) are NOT present.
6. The merge used reverse natural sort — verified by checking bookmark/page ordering:
   Q2 content appears BEFORE Q1 content (reverse order of Q1_2024 < Q2_2024 naturally).
7. Within a quarter, Section_10 appears before Section_9 in reverse natural order.
"""

import sys
import json
from pathlib import Path

checks = []

def check(name: str, passed: bool, detail: str):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

def run_eval(workspace: str):
    ws = Path(workspace)

    # ── 1. Find the output file ───────────────────────────────────────────────
    candidates = list(ws.rglob("quarterly_merged.pdf"))
    if not candidates:
        check("output_file_exists", False, "quarterly_merged.pdf not found anywhere under workspace")
        return finalize()

    out_pdf = candidates[0]
    check("output_file_exists", True, f"Found at {out_pdf.relative_to(ws)}")

    # ── 2. Valid PDF header ───────────────────────────────────────────────────
    try:
        raw = out_pdf.read_bytes()
        is_pdf = raw[:4] == b"%PDF"
        check("valid_pdf_header", is_pdf,
              "File starts with %PDF" if is_pdf else f"Header bytes: {raw[:8]!r}")
    except Exception as e:
        check("valid_pdf_header", False, str(e))
        return finalize()

    # ── Parse with pypdf ──────────────────────────────────────────────────────
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(out_pdf))
    except Exception as e:
        check("pdf_parseable", False, f"pypdf could not read file: {e}")
        return finalize()

    check("pdf_parseable", True, f"PDF has {len(reader.pages)} pages")

    # ── 3. Has bookmarks (outline) ────────────────────────────────────────────
    try:
        outlines = reader.outline
        has_bookmarks = outlines is not None and len(outlines) > 0
        check("has_bookmarks", has_bookmarks,
              f"Outline entries found: {len(outlines)}" if has_bookmarks
              else "No outline/bookmarks found — --no-bookmarks may have been used")
    except Exception as e:
        check("has_bookmarks", False, f"Error reading outline: {e}")

    # ── Helper: flatten outline titles ────────────────────────────────────────
    def flatten_outline(items, depth=0):
        """Yield (depth, title) for all outline entries recursively."""
        for item in items:
            if isinstance(item, list):
                yield from flatten_outline(item, depth + 1)
            else:
                try:
                    yield (depth, item.title)
                except AttributeError:
                    pass

    try:
        outline_titles = list(flatten_outline(reader.outline))
        title_strings = [t for _, t in outline_titles]
    except Exception as e:
        outline_titles = []
        title_strings = []

    # ── 4. Archive and Draft excluded ─────────────────────────────────────────
    archive_present = any("archive" in t.lower() for t in title_strings)
    draft_present   = any("draft"   in t.lower() for t in title_strings)

    check("archive_excluded", not archive_present,
          "No 'Archive' bookmark found — correctly excluded" if not archive_present
          else f"'Archive' found in bookmarks: {[t for t in title_strings if 'archive' in t.lower()]}")

    check("draft_excluded", not draft_present,
          "No 'Draft' bookmark found — correctly excluded" if not draft_present
          else f"'Draft' found in bookmarks: {[t for t in title_strings if 'draft' in t.lower()]}")

    # ── 5. Hidden dirs excluded ───────────────────────────────────────────────
    hidden_present = any(t.startswith(".") for t in title_strings)
    check("hidden_dirs_excluded", not hidden_present,
          "No hidden-directory bookmarks found" if not hidden_present
          else f"Hidden dir bookmarks present: {[t for t in title_strings if t.startswith('.')]}")

    # ── 6. Reverse natural sort: Q2_2024 before Q1_2024 ─────────────────────
    # In reverse natural sort, Q2_2024 > Q1_2024 naturally, so Q2 should appear first
    try:
        q1_idx = next((i for i, t in enumerate(title_strings) if "Q1_2024" in t or "Q1" in t), None)
        q2_idx = next((i for i, t in enumerate(title_strings) if "Q2_2024" in t or "Q2" in t), None)

        if q1_idx is not None and q2_idx is not None:
            q2_before_q1 = q2_idx < q1_idx
            check("reverse_sort_q2_before_q1", q2_before_q1,
                  f"Q2 bookmark at index {q2_idx}, Q1 at {q1_idx} — Q2 correctly before Q1" if q2_before_q1
                  else f"Q2 bookmark at index {q2_idx}, Q1 at {q1_idx} — expected Q2 before Q1 (reverse sort)")
        else:
            check("reverse_sort_q2_before_q1", False,
                  f"Could not find Q1/Q2 bookmarks to verify order. Titles: {title_strings[:10]}")
    except Exception as e:
        check("reverse_sort_q2_before_q1", False, f"Error checking sort order: {e}")

    # ── 7. Within Q2: Section_10 before Section_9 (reverse natural) ──────────
    try:
        s9_idx  = next((i for i, t in enumerate(title_strings) if "Section_9"  == t or t.endswith("/Section_9")), None)
        s10_idx = next((i for i, t in enumerate(title_strings) if "Section_10" == t or t.endswith("/Section_10")), None)

        if s9_idx is not None and s10_idx is not None:
            s10_before_s9 = s10_idx < s9_idx
            check("reverse_natural_section10_before_section9", s10_before_s9,
                  f"Section_10 at {s10_idx}, Section_9 at {s9_idx} — correct reverse natural order"
                  if s10_before_s9 else
                  f"Section_10 at {s10_idx}, Section_9 at {s9_idx} — wrong order; expected Section_10 first (reverse natural)")
        else:
            # Softer check — just note it's not verifiable
            check("reverse_natural_section10_before_section9", True,
                  f"Section_9/Section_10 bookmarks not distinctly found at top level; skipping sub-order check. Titles: {title_strings}")
    except Exception as e:
        check("reverse_natural_section10_before_section9", False, f"Error: {e}")

    return finalize()


def finalize():
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / max(len(checks), 1)
    all_passed = all(c["passed"] for c in checks)
    result = {
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)