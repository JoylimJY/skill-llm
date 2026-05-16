#!/usr/bin/env python3
"""
Evaluation script for the Relativity Deposition Question Builder task.
Usage: python eval_script.py /workspace
"""

import sys
import json
import re
from pathlib import Path

def find_output_file(workspace: Path) -> Path | None:
    """Locate deposition_questions.md anywhere in workspace."""
    matches = list(workspace.rglob("deposition_questions.md"))
    if matches:
        return matches[0]
    return None

def check_document_ids_present(content: str) -> tuple[bool, str]:
    """Check that the four expected document IDs (55, 89, 178, 289) appear as headings."""
    expected = {55, 89, 178, 289}
    found = set()
    # Look for ## Document ID: NNN or similar heading patterns
    for m in re.finditer(r'(?i)document\s+id\s*[:\-–]?\s*(\d+)', content):
        found.add(int(m.group(1)))
    missing = expected - found
    extra_wrong = {178+23, 201, 310, 142, 67}  # wrong IDs that would appear if dual-ID rule not applied
    false_positives = found & extra_wrong
    ok = len(missing) == 0 and len(false_positives) == 0
    detail = f"Expected IDs {sorted(expected)}, found {sorted(found)}."
    if missing:
        detail += f" Missing: {sorted(missing)}."
    if false_positives:
        detail += f" Wrong IDs present (dual-ID rule failure): {sorted(false_positives)}."
    return ok, detail

def check_wrong_ids_absent(content: str) -> tuple[bool, str]:
    """Confirm that IDs 201, 310, 142, 67 do NOT appear as document ID headings (would indicate wrong dual-ID selection)."""
    wrong_ids = {201, 310, 142, 67}
    found_wrong = set()
    for m in re.finditer(r'(?i)document\s+id\s*[:\-–]?\s*(\d+)', content):
        val = int(m.group(1))
        if val in wrong_ids:
            found_wrong.add(val)
    ok = len(found_wrong) == 0
    detail = f"Wrong document IDs (larger from dual-ID pairs) present as headings: {sorted(found_wrong)}." if found_wrong else "No incorrect dual-ID selections detected."
    return ok, detail

def check_ascending_order(content: str) -> tuple[bool, str]:
    """Check that document ID headings appear in ascending numeric order."""
    ids_in_order = []
    for m in re.finditer(r'(?i)document\s+id\s*[:\-–]?\s*(\d+)', content):
        ids_in_order.append(int(m.group(1)))
    if len(ids_in_order) < 2:
        return False, f"Not enough document ID headings found to verify order. Found: {ids_in_order}"
    is_sorted = ids_in_order == sorted(ids_in_order)
    detail = f"Document ID heading order: {ids_in_order}. {'Correct ascending order.' if is_sorted else 'NOT in ascending order.'}"
    return is_sorted, detail

def check_reason_sections(content: str) -> tuple[bool, str]:
    """Check that 'Reason why we ask this question' appears under questions."""
    count = len(re.findall(r'(?i)reason\s+why\s+we\s+ask\s+this\s+question', content))
    ok = count >= 4  # at least 4 questions across documents
    return ok, f"Found {count} 'Reason why we ask this question' sections (need >= 4)."

def check_quote_sections(content: str) -> tuple[bool, str]:
    """Check that quote sections appear under questions."""
    count = len(re.findall(r'(?i)quote\s+from\s+the\s+document\s+to\s+use\s+in\s+deposition', content))
    ok = count >= 4
    return ok, f"Found {count} 'Quote from the document' sections (need >= 4)."

def check_legal_theory_present(content: str) -> tuple[bool, str]:
    """Check that the output references the legal theory (fraudulent billing / upcoding)."""
    theory_keywords = ["upcode", "upcod", "fraudulent billing", "false claim", "billing fraud",
                       "medic", "cpT", "99215", "revenue"]
    content_lower = content.lower()
    found = [kw for kw in theory_keywords if kw.lower() in content_lower]
    ok = len(found) >= 2
    return ok, f"Legal theory keywords found: {found}."

def check_verbatim_quotes(content: str) -> tuple[bool, str]:
    """Check that at least one verbatim quote from the PDFs appears."""
    # Look for quoted text that resembles content from the generated PDFs
    smoking_gun_phrases = [
        "code up",
        "99215",
        "Green light",
        "make sure they support",
        "add clinical justification",
        "revenue per encounter",
        "coding training",
        "upcoding initiative",
        "motion carried",
        "billing optimization",
    ]
    found = [p for p in smoking_gun_phrases if p.lower() in content.lower()]
    ok = len(found) >= 2
    return ok, f"Verbatim PDF phrases found in quotes: {found}."

def check_no_merged_sections(content: str) -> tuple[bool, str]:
    """Check that document IDs are not merged (each expected ID has its own heading)."""
    # Each of 55, 89, 178, 289 must have a separate heading
    expected = [55, 89, 178, 289]
    headings = []
    for m in re.finditer(r'(?i)document\s+id\s*[:\-–]?\s*(\d+)', content):
        headings.append(int(m.group(1)))
    for eid in expected:
        if headings.count(eid) < 1:
            return False, f"Document ID {eid} does not have its own section heading. Headings found: {headings}"
    return True, f"All expected document IDs have separate sections: {[h for h in headings if h in expected]}"

def check_extraction_tool_used(workspace: Path) -> tuple[bool, str]:
    """Check whether the agent ran the extraction script (by looking for output JSON)."""
    json_matches = list(workspace.rglob("*.json"))
    # Filter out the distractor manifests
    candidate = [f for f in json_matches if "pages" in f.name.lower() or "relativity" in f.name.lower() or "extract" in f.name.lower()]
    if candidate:
        try:
            data = json.loads(candidate[0].read_text())
            if isinstance(data, list) and len(data) > 0 and "selected_document_id" in data[0]:
                return True, f"Extraction JSON found at {candidate[0]} with {len(data)} page records."
        except Exception as e:
            pass
    # Fallback: check any JSON with selected_document_id
    for jf in json_matches:
        try:
            data = json.loads(jf.read_text())
            if isinstance(data, list) and any("selected_document_id" in (r if isinstance(r, dict) else {}) for r in data):
                return True, f"Extraction JSON found at {jf}."
        except Exception:
            pass
    return False, "No extraction tool output JSON found. Agent may not have run scripts/extract_relativity_pages.py."

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    total_score = 0.0

    # ── Locate output file ──────────────────────────────────────────────────
    output_file = find_output_file(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"deposition_questions.md {'found at ' + str(output_file) if file_exists else 'NOT found anywhere in workspace'}."
    })

    if not file_exists:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result))
        return

    content = output_file.read_text(encoding="utf-8", errors="replace")

    # ── Run all checks ───────────────────────────────────────────────────────
    check_fns = [
        ("extraction_tool_used",       lambda: check_extraction_tool_used(workspace)),
        ("correct_document_ids_present", lambda: check_document_ids_present(content)),
        ("wrong_ids_absent",           lambda: check_wrong_ids_absent(content)),
        ("ascending_id_order",         lambda: check_ascending_order(content)),
        ("reason_sections_present",    lambda: check_reason_sections(content)),
        ("quote_sections_present",     lambda: check_quote_sections(content)),
        ("legal_theory_present",       lambda: check_legal_theory_present(content)),
        ("verbatim_quotes_present",    lambda: check_verbatim_quotes(content)),
        ("no_merged_id_sections",      lambda: check_no_merged_sections(content)),
    ]

    weights = {
        "extraction_tool_used":          0.10,
        "correct_document_ids_present":  0.20,   # critical: dual-ID rule
        "wrong_ids_absent":              0.15,   # critical: dual-ID rule
        "ascending_id_order":            0.10,
        "reason_sections_present":       0.10,
        "quote_sections_present":        0.10,
        "legal_theory_present":          0.10,
        "verbatim_quotes_present":       0.10,
        "no_merged_id_sections":         0.05,
    }

    for name, fn in check_fns:
        try:
            passed, detail = fn()
        except Exception as ex:
            passed, detail = False, f"Exception during check: {ex}"
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            total_score += weights.get(name, 0.0)

    # file_exists already checked; add its weight
    if file_exists:
        total_score += 0.0  # weight baked into other checks

    # Overall pass: must have correct IDs, no wrong IDs, reason+quote sections
    critical = ["correct_document_ids_present", "wrong_ids_absent",
                "reason_sections_present", "quote_sections_present"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)

    result = {
        "passed": critical_passed and total_score >= 0.55,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()