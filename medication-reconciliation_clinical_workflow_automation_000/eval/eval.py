#!/usr/bin/env python3
"""
Evaluation script for the medication reconciliation task.
Checks that the agent produced a correct reconciliation_report.json
for patient PT-00142 by running scripts/main.py with the right inputs.
"""
import sys
import json
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ── Helper ─────────────────────────────────────────────────────────────
    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        nonlocal total_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            total_score += weight

    MAX_SCORE = 10.0

    # ── 1. Locate the output file ──────────────────────────────────────────
    # Agent is told to produce "reconciliation_report.json"
    candidates = list(ws.rglob("reconciliation_report.json"))
    # Exclude the old PT-00130 report which is in a different path
    candidates = [p for p in candidates if "PT-00130" not in str(p)]

    if not candidates:
        add_check("output_file_exists", False,
                  "reconciliation_report.json not found anywhere in workspace.", 2.0)
        return checks, 0.0, MAX_SCORE

    report_path = candidates[0]
    add_check("output_file_exists", True,
              f"Found reconciliation_report.json at {report_path}", 2.0)

    # ── 2. Parse the JSON ──────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            data = json.load(f)
        add_check("output_valid_json", True, "File is valid JSON.", 1.0)
    except Exception as e:
        add_check("output_valid_json", False, f"JSON parse error: {e}", 1.0)
        return checks, total_score, MAX_SCORE

    # ── 3. Patient ID ──────────────────────────────────────────────────────
    pid = data.get("patient_id", "")
    if pid == "PT-00142":
        add_check("correct_patient_id", True, f"patient_id = {pid!r}", 1.0)
    else:
        add_check("correct_patient_id", False,
                  f"Expected patient_id='PT-00142', got {pid!r}", 1.0)

    # ── 4. Reconciliation block present ───────────────────────────────────
    recon = data.get("reconciliation", {})
    if recon:
        add_check("reconciliation_block_present", True,
                  "Top-level 'reconciliation' key is present.", 0.5)
    else:
        add_check("reconciliation_block_present", False,
                  "Missing top-level 'reconciliation' key.", 0.5)
        return checks, total_score, MAX_SCORE

    # ── 5. dose_changed: Metformin with exact warning string ───────────────
    dose_changed = recon.get("dose_changed", [])
    dc_drugs = [e.get("drug", "").strip().lower() for e in dose_changed]
    metformin_dc = next((e for e in dose_changed
                         if e.get("drug", "").strip().lower() == "metformin"), None)

    if metformin_dc:
        add_check("dose_changed_metformin_present", True,
                  f"Metformin correctly placed in dose_changed.", 1.5)
        expected_warning = "Dose change detected — verify with prescribing physician before proceeding."
        actual_warning = metformin_dc.get("warning", "")
        if actual_warning == expected_warning:
            add_check("dose_changed_exact_warning_string", True,
                      "Exact warning string matches.", 1.5)
        else:
            add_check("dose_changed_exact_warning_string", False,
                      f"Warning string mismatch.\nExpected: {expected_warning!r}\nGot:      {actual_warning!r}", 1.5)
        # Check dose values
        pre_dose = metformin_dc.get("pre_admission_dose", "")
        in_dose  = metformin_dc.get("inpatient_dose", "")
        if "500" in pre_dose and "1000" in in_dose:
            add_check("dose_changed_metformin_doses", True,
                      f"pre_admission_dose={pre_dose!r}, inpatient_dose={in_dose!r}", 0.5)
        else:
            add_check("dose_changed_metformin_doses", False,
                      f"Dose values incorrect: pre={pre_dose!r}, in={in_dose!r}", 0.5)
    else:
        add_check("dose_changed_metformin_present", False,
                  f"Metformin not found in dose_changed. dose_changed drugs: {dc_drugs}", 1.5)
        add_check("dose_changed_exact_warning_string", False,
                  "Cannot check warning string — Metformin not in dose_changed.", 1.5)
        add_check("dose_changed_metformin_doses", False,
                  "Cannot check dose values — Metformin not in dose_changed.", 0.5)

    # ── 6. discontinued: Lisinopril ────────────────────────────────────────
    discontinued = recon.get("discontinued", [])
    disc_drugs = [e.get("drug", "").strip().lower() for e in discontinued]
    if "lisinopril" in disc_drugs:
        add_check("discontinued_lisinopril", True,
                  "Lisinopril correctly placed in discontinued.", 1.0)
    else:
        add_check("discontinued_lisinopril", False,
                  f"Lisinopril not in discontinued. discontinued: {disc_drugs}", 1.0)

    # ── 7. new_medications: Heparin ────────────────────────────────────────
    new_meds = recon.get("new_medications", [])
    new_drugs = [e.get("drug", "").strip().lower() for e in new_meds]
    if "heparin" in new_drugs:
        add_check("new_medications_heparin", True,
                  "Heparin correctly placed in new_medications.", 1.0)
    else:
        add_check("new_medications_heparin", False,
                  f"Heparin not in new_medications. new_medications: {new_drugs}", 1.0)

    # ── 8. continued: Warfarin and Levetiracetam ───────────────────────────
    continued = recon.get("continued", [])
    cont_drugs = [e.get("drug", "").strip().lower() for e in continued]
    warfarin_ok      = "warfarin"      in cont_drugs
    levetiracetam_ok = "levetiracetam" in cont_drugs
    if warfarin_ok and levetiracetam_ok:
        add_check("continued_correct_drugs", True,
                  "Warfarin and Levetiracetam correctly in continued.", 1.0)
    else:
        missing = []
        if not warfarin_ok:      missing.append("Warfarin")
        if not levetiracetam_ok: missing.append("Levetiracetam")
        add_check("continued_correct_drugs", False,
                  f"Missing from continued: {missing}. continued drugs: {cont_drugs}", 1.0)

    # ── 9. Metformin NOT in continued ─────────────────────────────────────
    metformin_in_continued = "metformin" in cont_drugs
    if not metformin_in_continued:
        add_check("metformin_not_in_continued", True,
                  "Metformin correctly absent from continued (it has a dose change).", 0.5)
    else:
        add_check("metformin_not_in_continued", False,
                  "Metformin incorrectly placed in 'continued' despite dose change.", 0.5)

    # ── 10. warnings block — critical drug class alerts ────────────────────
    warnings = recon.get("warnings", [])
    if isinstance(warnings, list) and len(warnings) > 0:
        # Check at least one warning contains a recognized critical class word
        critical_keywords = ["anticoagulant", "hypoglycemic", "antihypertensive", "antiepileptic",
                              "DISCONTINUED", "new inpatient order"]
        has_critical = any(
            any(kw.lower() in str(w).lower() for kw in critical_keywords)
            for w in warnings
        )
        if has_critical:
            add_check("warnings_critical_classes", True,
                      f"Warnings block populated with critical class alerts ({len(warnings)} entries).", 1.0)
        else:
            add_check("warnings_critical_classes", False,
                      f"Warnings present but no recognized critical-class keywords. Warnings: {warnings}", 1.0)
    else:
        add_check("warnings_critical_classes", False,
                  "Warnings block is empty or missing.", 1.0)

    # ── 11. verbose matching_rationale block ──────────────────────────────
    if "matching_rationale" in data:
        add_check("verbose_rationale_present", True,
                  "matching_rationale block present (--verbose flag was used).", 1.0)
    else:
        add_check("verbose_rationale_present", False,
                  "matching_rationale block absent — --verbose flag may not have been used.", 1.0)

    return checks, total_score, MAX_SCORE


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided."}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    checks, score, max_score = run_checks(workspace)
    normalized = round(score / max_score, 4)
    passed = normalized >= 0.75  # Must score ≥75% to pass

    print(json.dumps({
        "passed":  passed,
        "score":   normalized,
        "checks":  checks
    }, indent=2))


if __name__ == "__main__":
    main()