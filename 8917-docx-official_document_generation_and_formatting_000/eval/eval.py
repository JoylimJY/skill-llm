import sys
import json
import subprocess
from pathlib import Path

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []

    # ── Check 1: A clean Markdown file was produced (no manual heading numbers) ──
    md_files = list(workspace.rglob("*.md"))
    # Filter out the original raw_draft.md and references files
    candidate_mds = [
        f for f in md_files
        if f.name != "raw_draft.md"
        and "references" not in str(f)
        and "archive" not in str(f)
        and "misc" not in str(f)
    ]

    clean_md_found = False
    clean_md_path = None
    manual_numbering_found = False

    # Also check if the agent may have directly used raw_draft.md (which has manual numbers)
    # We need to check what .docx was produced and its structure

    import re
    manual_number_patterns = [
        re.compile(r'^#{1,5}\s+[一二三四五六七八九十]+[、．.]'),   # ## 一、xxx
        re.compile(r'^#{1,5}\s+（[一二三四五六七八九十]+）'),         # ### （一）xxx
        re.compile(r'^#{1,5}\s+[（(]\d+[）)]'),                       # #### （1）xxx
        re.compile(r'^#{1,5}\s+\d+[\.．]'),                           # #### 1.xxx
    ]

    for md_file in candidate_mds:
        try:
            content = md_file.read_text(encoding="utf-8")
            has_manual = False
            for line in content.splitlines():
                for pat in manual_number_patterns:
                    if pat.match(line.strip()):
                        has_manual = True
                        break
            if not has_manual:
                clean_md_found = True
                clean_md_path = md_file
                break
            else:
                manual_numbering_found = True
        except Exception:
            pass

    # It's also acceptable if the agent cleaned raw_draft.md in place
    # Check if raw_draft.md itself was cleaned (unlikely since we told them to produce output files)
    # More importantly, check the actual docx/pdf outputs

    checks.append({
        "name": "clean_markdown_no_manual_numbers",
        "passed": clean_md_found,
        "detail": (
            f"Found clean Markdown at {clean_md_path}" if clean_md_found
            else f"No clean Markdown found (manual numbering detected: {manual_numbering_found}). "
                 "Headings must NOT contain manual numbers like '一、', '（一）', '1.' in Markdown source."
        )
    })

    # ── Check 2: output .docx exists ─────────────────────────────────────────
    docx_files = [
        f for f in workspace.rglob("*.docx")
        if "archive" not in str(f) and ".bak" not in str(f)
    ]

    target_docx = None
    # Prefer a file named something like work_plan or output (not raw_draft)
    for f in docx_files:
        target_docx = f
        break

    docx_exists = target_docx is not None
    checks.append({
        "name": "docx_output_exists",
        "passed": docx_exists,
        "detail": f"Found docx at {target_docx}" if docx_exists else "No .docx output file found in workspace."
    })

    # ── Check 3: output .pdf exists ──────────────────────────────────────────
    pdf_files = [
        f for f in workspace.rglob("*.pdf")
        if "archive" not in str(f)
    ]
    pdf_exists = len(pdf_files) > 0
    pdf_path = pdf_files[0] if pdf_files else None

    checks.append({
        "name": "pdf_output_exists",
        "passed": pdf_exists,
        "detail": f"Found PDF at {pdf_path}" if pdf_exists else "No .pdf output file found. The task requires BOTH .docx and .pdf outputs."
    })

    # ── Check 4: docx contains expected heading structure (auto-numbered) ────
    docx_structure_ok = False
    docx_detail = "No docx to inspect."

    if docx_exists:
        try:
            from docx import Document
            doc = Document(str(target_docx))
            full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

            # The script auto-numbers headings; we expect to find patterns like:
            # 一、总体要求  /  （一）强化市容  /  1.开展专项  /  （1）社区宣传
            expected_patterns = [
                re.compile(r'一[、．]'),          # First level-2 heading auto-numbered
                re.compile(r'[（(]一[）)]'),      # First level-3 heading auto-numbered
                re.compile(r'1[\.．]'),           # First level-4 heading auto-numbered
                re.compile(r'[（(]1[）)]'),       # First level-5 heading auto-numbered
            ]

            matched = sum(1 for pat in expected_patterns if pat.search(full_text))
            docx_structure_ok = matched >= 3  # at least 3 of 4 patterns found

            docx_detail = (
                f"Auto-numbering patterns found: {matched}/4. Full text snippet: {full_text[:300]}"
            )
        except Exception as e:
            docx_detail = f"Failed to read docx: {e}"

    checks.append({
        "name": "docx_contains_auto_numbered_headings",
        "passed": docx_structure_ok,
        "detail": docx_detail
    })

    # ── Check 5: docx contains the original content (not garbled) ────────────
    content_ok = False
    content_detail = "No docx to inspect."

    if docx_exists:
        try:
            from docx import Document
            doc = Document(str(target_docx))
            full_text = " ".join(p.text for p in doc.paragraphs)

            required_phrases = [
                "总体要求",
                "主要任务",
                "城市管理",
                "垃圾分类",
                "保障措施",
            ]
            found = [phrase for phrase in required_phrases if phrase in full_text]
            content_ok = len(found) >= 4
            content_detail = f"Found {len(found)}/{len(required_phrases)} required content phrases: {found}"
        except Exception as e:
            content_detail = f"Error reading docx content: {e}"

    checks.append({
        "name": "docx_preserves_original_content",
        "passed": content_ok,
        "detail": content_detail
    })

    # ── Check 6: pdf and docx share the same base stem (produced together) ───
    stem_match = False
    stem_detail = "Cannot verify stem match — missing docx or pdf."

    if docx_exists and pdf_exists:
        docx_stem = target_docx.stem.lower()
        pdf_stem = pdf_path.stem.lower()
        # LibreOffice names the PDF after the docx stem
        stem_match = (docx_stem == pdf_stem) or (pdf_stem in docx_stem) or (docx_stem in pdf_stem)
        stem_detail = f"docx stem='{docx_stem}', pdf stem='{pdf_stem}', match={stem_match}"

    checks.append({
        "name": "pdf_and_docx_share_stem",
        "passed": stem_match,
        "detail": stem_detail
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    weights = {
        "clean_markdown_no_manual_numbers": 0.20,
        "docx_output_exists": 0.15,
        "pdf_output_exists": 0.20,
        "docx_contains_auto_numbered_headings": 0.25,
        "docx_preserves_original_content": 0.15,
        "pdf_and_docx_share_stem": 0.05,
    }

    score = sum(
        weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights
    )
    passed = all(c["passed"] for c in checks)

    return {
        "passed": passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))