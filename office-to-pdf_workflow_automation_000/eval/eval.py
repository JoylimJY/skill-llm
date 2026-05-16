import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []

    # The 6 source files that must be converted
    expected_pdfs = [
        "NDA_Client_Acme_Corp.pdf",
        "ServiceAgreement_GlobalTech.pdf",
        "Amendment_3_TermSheet.pdf",
        "ExhibitA_FeeSchedule.pdf",
        "ExhibitB_Definitions.pdf",
        "PartnershipDeck_Meridian.pdf",
    ]

    # Files that must NOT be converted (distractors)
    forbidden_pdfs = [
        "TemplateMSA.pdf",
        "DraftBudget_Q4.pdf",
    ]

    # ── Check 1: All PDFs land inside output/pdf_archive ─────────────────────
    output_dir = ws / "output" / "pdf_archive"
    output_dir_exists = output_dir.is_dir()
    checks.append({
        "name": "output_dir_exists",
        "passed": output_dir_exists,
        "detail": f"Directory output/pdf_archive {'exists' if output_dir_exists else 'does NOT exist'}"
    })

    # ── Check 2–7: Each expected PDF is present in output/pdf_archive ─────────
    found_count = 0
    for pdf_name in expected_pdfs:
        target_path = output_dir / pdf_name
        found = target_path.is_file()
        valid_pdf = False
        detail = f"{pdf_name} not found in output/pdf_archive"

        if found:
            try:
                content = target_path.read_bytes()
                # A valid PDF starts with %PDF
                valid_pdf = content[:4] == b"%PDF"
                detail = (
                    f"{pdf_name} found, valid PDF header: {valid_pdf} "
                    f"(size: {len(content)} bytes)"
                )
            except Exception as e:
                detail = f"{pdf_name} found but could not be read: {e}"
        
        passed = found and valid_pdf
        if passed:
            found_count += 1
        checks.append({
            "name": f"pdf_present_{pdf_name}",
            "passed": passed,
            "detail": detail
        })

    # ── Check 8: All 6 PDFs converted (aggregate) ─────────────────────────────
    all_converted = found_count == len(expected_pdfs)
    checks.append({
        "name": "all_six_pdfs_converted",
        "passed": all_converted,
        "detail": f"{found_count}/{len(expected_pdfs)} target PDFs successfully converted and placed in output/pdf_archive"
    })

    # ── Check 9: Distractor office files were NOT converted ───────────────────
    no_forbidden = True
    forbidden_details = []
    for pdf_name in forbidden_pdfs:
        # Search anywhere in workspace
        found_anywhere = list(ws.rglob(pdf_name))
        if found_anywhere:
            no_forbidden = False
            forbidden_details.append(f"{pdf_name} found at {[str(p) for p in found_anywhere]}")
    
    checks.append({
        "name": "distractor_files_not_converted",
        "passed": no_forbidden,
        "detail": (
            "No forbidden PDF conversions detected"
            if no_forbidden
            else f"Forbidden conversions found: {'; '.join(forbidden_details)}"
        )
    })

    # ── Check 10: PDFs are in output/pdf_archive specifically (not just anywhere) ─
    misplaced = []
    for pdf_name in expected_pdfs:
        # Find ALL instances of this pdf in the workspace
        all_instances = list(ws.rglob(pdf_name))
        # Filter out the one in output/pdf_archive
        wrong_locations = [p for p in all_instances if p.parent != output_dir]
        if wrong_locations:
            misplaced.append(f"{pdf_name} also at {[str(p) for p in wrong_locations]}")
    
    pdfs_in_correct_location = len(misplaced) == 0
    checks.append({
        "name": "pdfs_only_in_output_dir",
        "passed": pdfs_in_correct_location,
        "detail": (
            "All PDFs are exclusively in output/pdf_archive"
            if pdfs_in_correct_location
            else f"PDFs found in wrong locations too: {'; '.join(misplaced)}"
        )
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weight: each of the 6 individual PDF checks = 1pt, aggregate = 1pt,
    # output_dir_exists = 0.5pt, no_forbidden = 1pt, correct_location = 0.5pt
    # Total = 10 pts
    weights = {
        "output_dir_exists": 0.5,
        "all_six_pdfs_converted": 1.0,
        "distractor_files_not_converted": 1.0,
        "pdfs_only_in_output_dir": 0.5,
    }
    for pdf_name in expected_pdfs:
        weights[f"pdf_present_{pdf_name}"] = 1.0

    total_weight = sum(weights.values())
    earned = sum(weights.get(c["name"], 0) for c in checks if c["passed"])
    score = round(earned / total_weight, 4)

    overall_passed = all_converted and output_dir_exists and no_forbidden and pdfs_in_correct_location

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crashed", "passed": False, "detail": str(e)}]
        }
    print(json.dumps(result, indent=2))