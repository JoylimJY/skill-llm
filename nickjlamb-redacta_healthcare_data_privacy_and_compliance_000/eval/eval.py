import sys
import json
import re
from pathlib import Path

def find_output(workspace: Path):
    """Find the redacted output file."""
    # Check the specified staging path first
    primary = workspace / "nlp_pipeline/input_staging/discharge_letter_fielding_redacted.txt"
    if primary.exists():
        return primary
    # Fallback: search anywhere in workspace
    candidates = list(workspace.rglob("discharge_letter_fielding_redacted.txt"))
    if candidates:
        return candidates[0]
    return None


def run_checks(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []

    output_path = find_output(workspace)

    # ── Check 0: Output file exists ────────────────────────────────────────
    if output_path is None:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "discharge_letter_fielding_redacted.txt not found anywhere in workspace."})
        return checks

    checks.append({"name": "output_file_exists", "passed": True,
                   "detail": f"Found at {output_path}"})

    try:
        content = output_path.read_text()
    except Exception as e:
        checks.append({"name": "output_readable", "passed": False, "detail": str(e)})
        return checks

    checks.append({"name": "output_readable", "passed": True, "detail": "File read successfully."})

    # ── Check 1: Original patient identifiers NOT present ──────────────────
    forbidden_patterns = [
        (r"Dorothy\s+Fielding", "Patient name 'Dorothy Fielding'"),
        (r"\bFielding\b", "Patient surname 'Fielding'"),
        (r"485\s*777\s*3606", "Valid NHS number 485 777 3606"),
        (r"123\s*456\s*7890", "Invalid-Mod11 NHS ref 123 456 7890"),
        (r"RXH-3849201", "Hospital number RXH-3849201"),
        (r"AB\s*123456\s*C", "NI number AB123456C"),
        (r"07821\s*334\s*991", "Mobile number 07821 334 991"),
        (r"0113\s*265\s*8847", "Alternative tel 0113 265 8847"),
        (r"dorothy\.fielding@btinternet\.com", "Patient email"),
        (r"47\s+Balmoral\s+Crescent", "Patient address"),
        (r"LS7\s*4NP", "Patient postcode LS7 4NP"),
        (r"12/08/1954", "Date of birth 12/08/1954"),
    ]
    all_forbidden_ok = True
    for pattern, label in forbidden_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            checks.append({"name": f"no_raw_PII_{label.replace(' ', '_')[:30]}",
                           "passed": False,
                           "detail": f"Raw PII still present in output: {label}"})
            all_forbidden_ok = False
    if all_forbidden_ok:
        checks.append({"name": "no_raw_PII_in_output", "passed": True,
                       "detail": "No raw patient identifiers found in output."})

    # ── Check 2: Correct tokens present ────────────────────────────────────
    required_tokens = [
        (r"\[PATIENT_NAME\]", "PATIENT_NAME token"),
        (r"\[DATE_OF_BIRTH\]", "DATE_OF_BIRTH token"),
        (r"\[NHS_NUMBER\]", "NHS_NUMBER token"),
        (r"\[HOSPITAL_NUMBER\]", "HOSPITAL_NUMBER token"),
        (r"\[NI_NUMBER\]", "NI_NUMBER token"),
        (r"\[POSTCODE\]", "POSTCODE token"),
        (r"\[PHONE_NUMBER\]", "PHONE_NUMBER token"),
        (r"\[EMAIL\]", "EMAIL token"),
        (r"\[ADDRESS\]", "ADDRESS token"),
        (r"\[AGE\]", "AGE token"),
    ]
    for pattern, label in required_tokens:
        found = bool(re.search(pattern, content))
        checks.append({"name": f"token_present_{label.replace(' ', '_')}",
                       "passed": found,
                       "detail": f"{label} {'found' if found else 'MISSING'} in output."})

    # ── Check 3: PATIENT_NAME appears at least 3 times (3 references) ──────
    patient_name_count = len(re.findall(r"\[PATIENT_NAME\]", content))
    checks.append({
        "name": "patient_name_token_count_gte_3",
        "passed": patient_name_count >= 3,
        "detail": f"[PATIENT_NAME] appears {patient_name_count} times (expected ≥3 for consistency rule)."
    })

    # ── Check 4: NHS_NUMBER appears at least 2 times (both numbers redacted) ─
    nhs_count = len(re.findall(r"\[NHS_NUMBER\]", content))
    checks.append({
        "name": "both_nhs_numbers_redacted",
        "passed": nhs_count >= 2,
        "detail": f"[NHS_NUMBER] appears {nhs_count} times (expected ≥2: one valid + one uncertain)."
    })

    # ── Check 5: Clinician names preserved ─────────────────────────────────
    thornton_present = bool(re.search(r"Dr\.?\s*Amelia\s*Thornton", content, re.IGNORECASE))
    kapoor_present = bool(re.search(r"Mr\.?\s*Rajiv\s*Kapoor", content, re.IGNORECASE))
    checks.append({
        "name": "clinician_thornton_preserved",
        "passed": thornton_present,
        "detail": "Dr. Amelia Thornton " + ("preserved ✓" if thornton_present else "WRONGLY REDACTED ✗")
    })
    checks.append({
        "name": "clinician_kapoor_preserved",
        "passed": kapoor_present,
        "detail": "Mr. Rajiv Kapoor " + ("preserved ✓" if kapoor_present else "WRONGLY REDACTED ✗")
    })

    # ── Check 6: Clinical/appointment dates preserved (not over-redacted) ──
    preserved_dates = [
        (r"18\s+June\s+2026|18/06/2026", "admission date 18 June 2026"),
        (r"21\s+June\s+2026|21/06/2026", "procedure date 21 June 2026"),
        (r"22\s+June\s+2026|22/06/2026", "echo date 22 June 2026"),
        (r"5\s+August\s+2026|05/08/2026|5\s+Aug\s+2026", "follow-up date 5 August 2026"),
        (r"26\s+June\s+2026|26/06/2026", "letter date 26 June 2026"),
    ]
    for pattern, label in preserved_dates:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        checks.append({
            "name": f"clinical_date_preserved_{label[:30].replace(' ', '_')}",
            "passed": found,
            "detail": f"Clinical date '{label}' {'preserved ✓' if found else 'WRONGLY REDACTED ✗'}"
        })

    # ── Check 7: Hospital/institution name preserved ────────────────────────
    hospital_present = bool(re.search(r"St\.?\s*James", content, re.IGNORECASE))
    checks.append({
        "name": "hospital_name_preserved",
        "passed": hospital_present,
        "detail": "St. James's University Hospital " + ("preserved ✓" if hospital_present else "WRONGLY REDACTED ✗")
    })

    # ── Check 8: Redaction Report section present ──────────────────────────
    has_report = bool(re.search(r"Redaction\s+Report", content, re.IGNORECASE))
    checks.append({
        "name": "redaction_report_section_present",
        "passed": has_report,
        "detail": "Redaction Report section " + ("found ✓" if has_report else "MISSING ✗")
    })

    # ── Check 9: Report lists token types with counts ──────────────────────
    if has_report:
        report_section = content[content.lower().find("redaction report"):]
        has_nhs_in_report = bool(re.search(r"NHS_NUMBER.*×\s*\d+|\[NHS_NUMBER\]", report_section))
        has_patient_in_report = bool(re.search(r"PATIENT_NAME.*×\s*\d+|\[PATIENT_NAME\]", report_section))
        has_items_count = bool(re.search(r"Items\s+pseudonymised\s*:\s*\d+", report_section, re.IGNORECASE))
        checks.append({
            "name": "report_lists_nhs_number_token",
            "passed": has_nhs_in_report,
            "detail": "NHS_NUMBER listed in Redaction Report: " + ("yes ✓" if has_nhs_in_report else "no ✗")
        })
        checks.append({
            "name": "report_lists_patient_name_token",
            "passed": has_patient_in_report,
            "detail": "PATIENT_NAME listed in Redaction Report: " + ("yes ✓" if has_patient_in_report else "no ✗")
        })
        checks.append({
            "name": "report_has_items_pseudonymised_count",
            "passed": has_items_count,
            "detail": "'Items pseudonymised: N' line in report: " + ("found ✓" if has_items_count else "MISSING ✗")
        })

        # Report should name preserved clinicians
        report_names_clinician = bool(
            re.search(r"Thornton|Kapoor", report_section, re.IGNORECASE)
        )
        checks.append({
            "name": "report_names_preserved_clinicians",
            "passed": report_names_clinician,
            "detail": "Preserved clinicians named in report: " + ("yes ✓" if report_names_clinician else "no ✗")
        })
    else:
        for sub in ["report_lists_nhs_number_token", "report_lists_patient_name_token",
                    "report_has_items_pseudonymised_count", "report_names_preserved_clinicians"]:
            checks.append({"name": sub, "passed": False, "detail": "Redaction Report section absent."})

    # ── Check 10: POSTCODE appears at least twice (LS7 4NP + possibly LS9 7TF) ─
    # LS9 7TF is the hospital postcode — institutional, may or may not be redacted
    # LS7 4NP is definitely patient postcode → must be redacted
    # We just require ≥1 POSTCODE token
    postcode_count = len(re.findall(r"\[POSTCODE\]", content))
    checks.append({
        "name": "postcode_token_present_at_least_once",
        "passed": postcode_count >= 1,
        "detail": f"[POSTCODE] appears {postcode_count} times."
    })

    # ── Check 11: At least 2 PHONE_NUMBER tokens (mobile + landline 0113 265 8847)
    # (cardio secretariat 0113 206 5320 may also be redacted or kept — institutional)
    phone_count = len(re.findall(r"\[PHONE_NUMBER\]", content))
    checks.append({
        "name": "phone_number_token_count_gte_2",
        "passed": phone_count >= 2,
        "detail": f"[PHONE_NUMBER] appears {phone_count} times (expected ≥2 for patient mobile + landline)."
    })

    # ── Check 12: EMAIL appears at least once (patient email) ─────────────
    # cardio.secretary email is institutional — may or may not be redacted; we just need patient one gone
    email_count = len(re.findall(r"\[EMAIL\]", content))
    checks.append({
        "name": "email_token_present",
        "passed": email_count >= 1,
        "detail": f"[EMAIL] appears {email_count} times."
    })

    return checks


def main():
    workspace_str = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = run_checks(workspace_str)

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall = score >= 0.80  # require 80% of checks to pass

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()