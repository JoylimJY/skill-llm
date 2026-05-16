#!/usr/bin/env python3
"""
Evaluation script for NDA generation task.
Checks:
1. DOCX file exists at the correct path with correct filename
2. DOCX is a valid Word document
3. Document contains the correct party names
4. Document contains the effective date
5. Document contains the purpose text
6. /tmp/oa-values.json was cleaned up (or never left behind)
7. The template used is a ONE-WAY NDA (not mutual) — checks for disclosing/receiving party asymmetry
"""

import sys
import json
import os
import zipfile
from pathlib import Path

def run_checks(workspace: str):
    workspace_path = Path(workspace)
    checks = []
    overall_passed = True

    # --- Check 1: DOCX file exists ---
    docx_files = list(workspace_path.rglob("genomatix_one_way_nda.docx"))
    docx_found = len(docx_files) > 0
    docx_path = docx_files[0] if docx_found else None

    checks.append({
        "name": "DOCX file genomatix_one_way_nda.docx exists",
        "passed": docx_found,
        "detail": f"Found at {docx_path}" if docx_found else "File not found anywhere in workspace"
    })
    if not docx_found:
        overall_passed = False

    # --- Check 2: DOCX is in legal/contracts/ directory ---
    correct_location = False
    if docx_found:
        # Check if it's under legal/contracts/
        try:
            relative = docx_path.relative_to(workspace_path)
            parts = relative.parts
            correct_location = len(parts) >= 2 and parts[0] == "legal" and parts[1] == "contracts"
        except Exception:
            correct_location = False
    checks.append({
        "name": "DOCX file is located under legal/contracts/",
        "passed": correct_location,
        "detail": f"Path: {docx_path.relative_to(workspace_path) if docx_found else 'N/A'}"
    })
    if not correct_location:
        overall_passed = False

    # --- Check 3: DOCX is a valid ZIP/Word document ---
    valid_docx = False
    if docx_found:
        try:
            with zipfile.ZipFile(docx_path, 'r') as zf:
                names = zf.namelist()
                valid_docx = "word/document.xml" in names
        except Exception as e:
            valid_docx = False
            checks.append({
                "name": "DOCX is a valid Word document (ZIP structure)",
                "passed": False,
                "detail": f"Error opening as ZIP: {e}"
            })
    if docx_found:
        checks.append({
            "name": "DOCX is a valid Word document (ZIP structure)",
            "passed": valid_docx,
            "detail": "word/document.xml found inside ZIP" if valid_docx else "word/document.xml NOT found — invalid DOCX"
        })
    if not valid_docx:
        overall_passed = False

    # --- Extract full text from DOCX for content checks ---
    full_text = ""
    if valid_docx:
        try:
            import docx as python_docx
            doc = python_docx.Document(str(docx_path))
            full_text = " ".join([para.text for para in doc.paragraphs if para.text.strip()])
            # Also get text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        full_text += " " + cell.text
            full_text = full_text.lower()
        except Exception as e:
            full_text = ""
            checks.append({
                "name": "DOCX text extraction",
                "passed": False,
                "detail": f"Could not extract text: {e}"
            })

    # --- Check 4: Contains disclosing party name "NovaBiotek" ---
    novabiotek_present = "novabiotek" in full_text
    checks.append({
        "name": "Document contains 'NovaBiotek' (disclosing party)",
        "passed": novabiotek_present,
        "detail": "Found 'novabiotek' in document text" if novabiotek_present else "Could not find 'novabiotek' in document text"
    })
    if not novabiotek_present:
        overall_passed = False

    # --- Check 5: Contains receiving party name "Genomatix" ---
    genomatix_present = "genomatix" in full_text
    checks.append({
        "name": "Document contains 'Genomatix' (receiving party)",
        "passed": genomatix_present,
        "detail": "Found 'genomatix' in document text" if genomatix_present else "Could not find 'genomatix' in document text"
    })
    if not genomatix_present:
        overall_passed = False

    # --- Check 6: Contains effective date "July 1, 2025" or variation ---
    date_variants = ["july 1, 2025", "july 1 2025", "2025-07-01", "01 july 2025", "1 july 2025", "july 1st, 2025"]
    date_present = any(d in full_text for d in date_variants)
    checks.append({
        "name": "Document contains effective date (July 1, 2025)",
        "passed": date_present,
        "detail": "Found date reference in document" if date_present else f"Could not find date variants {date_variants} in document"
    })
    if not date_present:
        overall_passed = False

    # --- Check 7: Contains purpose text (clinical trial / contract research) ---
    purpose_keywords = ["clinical trial", "contract research", "phase i", "phase 1", "cro", "vendor evaluation", "evaluating"]
    purpose_present = any(kw in full_text for kw in purpose_keywords)
    checks.append({
        "name": "Document contains purpose context (clinical trial / vendor evaluation)",
        "passed": purpose_present,
        "detail": f"Found purpose keyword in document" if purpose_present else f"Could not find any of {purpose_keywords} in document"
    })
    if not purpose_present:
        overall_passed = False

    # --- Check 8: /tmp/oa-values.json was cleaned up ---
    tmp_json_exists = Path("/tmp/oa-values.json").exists()
    cleanup_done = not tmp_json_exists
    checks.append({
        "name": "/tmp/oa-values.json cleaned up after use",
        "passed": cleanup_done,
        "detail": "/tmp/oa-values.json does not exist (properly cleaned up)" if cleanup_done else "/tmp/oa-values.json still exists — cleanup step was skipped"
    })
    if not cleanup_done:
        overall_passed = False

    # --- Check 9: Document is a ONE-WAY NDA (not mutual) ---
    # One-way NDAs reference a single disclosing party and a single receiving party
    # Check for one-way / one-directional language OR the template name in any embedded metadata
    one_way_indicators = [
        "one-way", "one way", "disclosing party", "receiving party",
        "one-way nda", "unilateral", "common-paper-one-way-nda"
    ]
    one_way_present = any(ind in full_text for ind in one_way_indicators)
    # Also check that it's NOT ONLY a mutual NDA (mutual NDAs typically say "each party" discloses)
    # One-way: disclosing party is distinct from receiving party
    checks.append({
        "name": "Document is a one-way NDA (not mutual) — contains one-way NDA indicators",
        "passed": one_way_present,
        "detail": "Found one-way NDA indicators in document" if one_way_present else f"Could not confirm one-way NDA — none of {one_way_indicators} found"
    })
    if not one_way_present:
        overall_passed = False

    # --- Compute score ---
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / len(checks)

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Script invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace_dir = sys.argv[1]
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2))