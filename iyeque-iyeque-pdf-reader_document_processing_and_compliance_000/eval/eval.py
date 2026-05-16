import sys
import json
import re
from pathlib import Path

def main(workspace: str):
    ws = Path(workspace)
    checks = []
    overall_passed = True

    # ── Locate the output file ───────────────────────────────────────────────
    candidates = list(ws.rglob("audit_report.json"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "audit_report.json exists",
        "passed": file_found,
        "detail": str(candidates[0]) if file_found else "File not found anywhere in workspace"
    })
    if not file_found:
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    report_path = candidates[0]

    # ── Parse JSON ───────────────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "Valid JSON", "passed": False, "detail": str(e)})
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "Valid JSON", "passed": True, "detail": "Parsed successfully"})

    # ── Load reference data ──────────────────────────────────────────────────
    try:
        ref = json.loads((ws / "config" / "_trial_ref.json").read_text())
    except Exception as e:
        checks.append({"name": "Reference data readable", "passed": False, "detail": str(e)})
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── Check top-level structure: must be a list or dict with 3 entries ─────
    EXPECTED_FILES = ["trial_CT2024_001.pdf", "trial_CT2024_002.pdf", "trial_CT2024_003.pdf"]

    # Normalise: accept list or dict
    if isinstance(data, list):
        entries = data
        def get_entry(fname):
            for e in entries:
                if isinstance(e, dict):
                    v = e.get("filename","") or e.get("file","") or e.get("document","") or ""
                    if fname in v or fname == v:
                        return e
            return None
    elif isinstance(data, dict):
        entries = list(data.values())
        def get_entry(fname):
            for k, v in data.items():
                if fname in k:
                    return v
            return None
    else:
        checks.append({"name": "Report structure is list or dict", "passed": False,
                        "detail": f"Got {type(data)}"})
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    has_three = len(entries) == 3
    checks.append({
        "name": "Report contains exactly 3 document entries",
        "passed": has_three,
        "detail": f"Found {len(entries)} entries"
    })
    if not has_three:
        overall_passed = False

    # ── Per-document checks ──────────────────────────────────────────────────
    EXPECTED_TITLES = {
        "trial_CT2024_001.pdf": "Phase III Efficacy of Compound XR-77 in Hypertension",
        "trial_CT2024_002.pdf": "Safety Profile of BioAgent MR-22 in Type-2 Diabetes",
        "trial_CT2024_003.pdf": "Pharmacokinetics of Oral Formulation ZL-9 in Paediatric Cohort",
    }
    EXPECTED_AUTHORS = {
        "trial_CT2024_001.pdf": "Dr. Elena Marchetti",
        "trial_CT2024_002.pdf": "Prof. Takeshi Yamamoto",
        "trial_CT2024_003.pdf": "Dr. Amara Osei-Bonsu",
    }
    # Text that MUST appear in the 2-page extract
    MUST_CONTAIN = {
        "trial_CT2024_001.pdf": ["ABSTRACT", "XR-77", "METHODS"],
        "trial_CT2024_002.pdf": ["EXECUTIVE SUMMARY", "MR-22", "PATIENT POPULATION"],
        "trial_CT2024_003.pdf": ["SYNOPSIS", "ZL-9", "PK PARAMETERS (SINGLE DOSE)"],
    }
    # Text that must NOT appear (from page 3+)
    MUST_NOT_CONTAIN = {
        "trial_CT2024_001.pdf": ["CONCLUSION", "RESULTS"],
        "trial_CT2024_002.pdf": ["ADVERSE EVENTS TABLE", "REGULATORY IMPLICATIONS"],
        "trial_CT2024_003.pdf": ["PK PARAMETERS (MULTIPLE DOSE)", "CONCLUSIONS"],
    }

    doc_scores = []
    for fname in EXPECTED_FILES:
        entry = get_entry(fname)
        if entry is None:
            checks.append({"name": f"{fname}: entry found", "passed": False, "detail": "Not found in report"})
            overall_passed = False
            doc_scores.append(0)
            continue
        checks.append({"name": f"{fname}: entry found", "passed": True, "detail": "OK"})
        doc_score = 0

        # Check title (from metadata command)
        exp_title = EXPECTED_TITLES[fname]
        found_title = ""
        for field in ["title", "metadata"]:
            v = entry.get(field, "")
            if isinstance(v, dict):
                found_title = v.get("title", "")
            elif isinstance(v, str):
                found_title = v
        title_ok = exp_title.lower() in found_title.lower() if found_title else False
        checks.append({
            "name": f"{fname}: title matches metadata",
            "passed": title_ok,
            "detail": f"Expected: '{exp_title}', Got: '{found_title}'"
        })
        if not title_ok:
            overall_passed = False
        else:
            doc_score += 1

        # Check author (from metadata command)
        exp_author = EXPECTED_AUTHORS[fname]
        found_author = ""
        for field in ["author", "metadata"]:
            v = entry.get(field, "")
            if isinstance(v, dict):
                found_author = v.get("author", "")
            elif isinstance(v, str) and field == "author":
                found_author = v
        author_ok = exp_author.lower() in found_author.lower() if found_author else False
        checks.append({
            "name": f"{fname}: author matches metadata",
            "passed": author_ok,
            "detail": f"Expected: '{exp_author}', Got: '{found_author}'"
        })
        if not author_ok:
            overall_passed = False
        else:
            doc_score += 1

        # Check text content (must come from max_pages=2 extract)
        text_field = entry.get("text", "") or entry.get("content", "") or entry.get("extract", "") or ""
        if isinstance(text_field, list):
            text_field = " ".join(text_field)

        # Must contain (pages 1 & 2)
        for keyword in MUST_CONTAIN[fname]:
            kw_ok = keyword.lower() in text_field.lower()
            checks.append({
                "name": f"{fname}: extracted text contains '{keyword}'",
                "passed": kw_ok,
                "detail": "Found" if kw_ok else f"Missing. Text length: {len(text_field)}"
            })
            if not kw_ok:
                overall_passed = False
            else:
                doc_score += 1

        # Must NOT contain (pages 3+) — proves max_pages=2 was respected
        for keyword in MUST_NOT_CONTAIN[fname]:
            kw_absent = keyword.lower() not in text_field.lower()
            checks.append({
                "name": f"{fname}: page-3+ content '{keyword}' is absent (max_pages=2 respected)",
                "passed": kw_absent,
                "detail": "Correctly absent" if kw_absent else f"Found (agent extracted too many pages)"
            })
            if not kw_absent:
                overall_passed = False
            else:
                doc_score += 1

        doc_scores.append(doc_score)

    # ── Score calculation ────────────────────────────────────────────────────
    # Per doc: 1 (found) + 1 (title) + 1 (author) + 3 (must-contain) + 2 (must-not) = 8 possible
    max_per_doc = 7  # title + author + 3 must-contain + 2 must-not
    total_possible = 3 * max_per_doc + 1  # +1 for 3-entry structure check
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(passed_checks / len(checks), 3)

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False, "detail": "Usage: eval.py <workspace>"}]}))
        sys.exit(1)
    main(sys.argv[1])