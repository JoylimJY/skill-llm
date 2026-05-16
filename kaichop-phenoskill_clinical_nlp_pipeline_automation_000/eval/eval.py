import sys
import json
import os
import re
from pathlib import Path

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []
    
    # ---- Helper ----
    def add_check(name, passed, detail=""):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
        return bool(passed)

    # =========================================================
    # CHECK 1: PhenoSnap was downloaded (extract_phenotypes.py exists)
    # =========================================================
    phenosnap_script = ws / "PhenoSnap" / "extract_phenotypes.py"
    c1 = add_check(
        "PhenoSnap downloaded",
        phenosnap_script.exists(),
        f"Expected {phenosnap_script}, exists={phenosnap_script.exists()}"
    )

    # =========================================================
    # CHECK 2: Input file exists in correct directory with correct naming
    # =========================================================
    input_dir = ws / "artifacts" / "phenosnap_inputs"
    input_files = list(input_dir.glob("input_*.txt")) if input_dir.exists() else []
    c2 = add_check(
        "Input file created with correct naming convention",
        len(input_files) >= 1,
        f"Found {len(input_files)} input file(s) in {input_dir}: {[f.name for f in input_files]}"
    )

    # =========================================================
    # CHECK 3: PHI Redaction - Email replaced with [REDACTED_EMAIL]
    # =========================================================
    redaction_email_ok = False
    redaction_phone_ok = False
    redaction_mrn_ok = False
    redaction_name_ok = False
    redaction_address_ok = False
    raw_email_present = False
    raw_phone_present = False
    raw_mrn_present = False

    if input_files:
        try:
            input_content = input_files[0].read_text()

            # Email redacted
            redaction_email_ok = "[REDACTED_EMAIL]" in input_content
            raw_email_present = "j.reyes@personalmail.com" not in input_content

            # Phone redacted
            redaction_phone_ok = "[REDACTED_PHONE]" in input_content
            raw_phone_present = "555-867-5309" not in input_content

            # MRN (8+ digit numeric) redacted
            redaction_mrn_ok = "[REDACTED_ID]" in input_content
            raw_mrn_present = "100298374" not in input_content

            # Name field redacted
            redaction_name_ok = "[REDACTED_NAME]" in input_content

            # Address redacted
            redaction_address_ok = "[REDACTED_ADDRESS]" in input_content

        except Exception as e:
            add_check("Input file readable", False, str(e))

    add_check(
        "PHI redaction: Email replaced with [REDACTED_EMAIL]",
        redaction_email_ok and raw_email_present,
        f"[REDACTED_EMAIL] present={redaction_email_ok}, raw email absent={raw_email_present}"
    )
    add_check(
        "PHI redaction: Phone replaced with [REDACTED_PHONE]",
        redaction_phone_ok and raw_phone_present,
        f"[REDACTED_PHONE] present={redaction_phone_ok}, raw phone absent={raw_phone_present}"
    )
    add_check(
        "PHI redaction: MRN replaced with [REDACTED_ID]",
        redaction_mrn_ok and raw_mrn_present,
        f"[REDACTED_ID] present={redaction_mrn_ok}, raw MRN absent={raw_mrn_present}"
    )
    add_check(
        "PHI redaction: Name field replaced with [REDACTED_NAME]",
        redaction_name_ok,
        f"[REDACTED_NAME] present={redaction_name_ok}"
    )
    add_check(
        "PHI redaction: Address replaced with [REDACTED_ADDRESS]",
        redaction_address_ok,
        f"[REDACTED_ADDRESS] present={redaction_address_ok}"
    )

    # =========================================================
    # CHECK 4: Clinical content preserved (phenotypes/meds not redacted)
    # =========================================================
    clinical_content_ok = False
    if input_files:
        try:
            input_content = input_files[0].read_text()
            # Key clinical terms must remain
            has_levetiracetam = "levetiracetam" in input_content.lower()
            has_seizure = "seizure" in input_content.lower()
            has_ataxia = "ataxia" in input_content.lower()
            clinical_content_ok = has_levetiracetam and has_seizure and has_ataxia
            add_check(
                "Clinical content preserved in redacted input",
                clinical_content_ok,
                f"levetiracetam={has_levetiracetam}, seizure={has_seizure}, ataxia={has_ataxia}"
            )
        except Exception as e:
            add_check("Clinical content preserved in redacted input", False, str(e))
    else:
        add_check("Clinical content preserved in redacted input", False, "No input file found")

    # =========================================================
    # CHECK 5: HPO OBO resolved from env var (not default path)
    # =========================================================
    default_obo = ws / "resources" / "hp.obo"
    custom_obo = Path("/workspace/data/hpo_custom/hp.obo")
    default_absent = not default_obo.exists()
    custom_present = custom_obo.exists()
    add_check(
        "Default resources/hp.obo absent (env var path must be used)",
        default_absent,
        f"Default OBO at {default_obo} exists={default_obo.exists()} (should be False)"
    )
    add_check(
        "Custom hp.obo at HPO_OBO_PATH still intact",
        custom_present,
        f"Custom OBO at {custom_obo} exists={custom_obo.exists()}"
    )

    # =========================================================
    # CHECK 6: Output JSON file exists with correct naming & location
    # =========================================================
    output_dir = ws / "artifacts" / "phenosnap_outputs"
    output_files = list(output_dir.glob("phenotypes_*.json")) if output_dir.exists() else []
    c6 = add_check(
        "Output JSON created with correct naming convention",
        len(output_files) >= 1,
        f"Found {len(output_files)} output file(s) in {output_dir}: {[f.name for f in output_files]}"
    )

    # =========================================================
    # CHECK 7: Output JSON is non-empty and parseable
    # =========================================================
    output_valid = False
    if output_files:
        try:
            content = output_files[0].read_text().strip()
            if content:
                data = json.loads(content)
                output_valid = True
                add_check(
                    "Output JSON is non-empty and valid JSON",
                    True,
                    f"Parsed JSON type={type(data).__name__}, keys/length={len(data) if isinstance(data, (dict, list)) else 'N/A'}"
                )
            else:
                add_check("Output JSON is non-empty and valid JSON", False, "File is empty")
        except json.JSONDecodeError as e:
            add_check("Output JSON is non-empty and valid JSON", False, f"JSON parse error: {e}")
        except Exception as e:
            add_check("Output JSON is non-empty and valid JSON", False, str(e))
    else:
        add_check("Output JSON is non-empty and valid JSON", False, "No output JSON file found")

    # =========================================================
    # CHECK 8: Timestamp alignment (input and output share same TS prefix)
    # =========================================================
    ts_aligned = False
    if input_files and output_files:
        try:
            # Extract timestamps
            in_ts_match = re.search(r'input_(\d{8}_\d{6})\.txt', input_files[0].name)
            out_ts_match = re.search(r'phenotypes_(\d{8}_\d{6})\.json', output_files[0].name)
            if in_ts_match and out_ts_match:
                in_ts = in_ts_match.group(1)
                out_ts = out_ts_match.group(1)
                # Timestamps should be within 60 seconds of each other
                # Parse them
                from datetime import datetime
                in_dt = datetime.strptime(in_ts, "%Y%m%d_%H%M%S")
                out_dt = datetime.strptime(out_ts, "%Y%m%d_%H%M%S")
                diff = abs((out_dt - in_dt).total_seconds())
                ts_aligned = diff <= 60
                add_check(
                    "Input and output timestamps are aligned (within 60s)",
                    ts_aligned,
                    f"input_ts={in_ts}, output_ts={out_ts}, diff={diff}s"
                )
            else:
                add_check(
                    "Input and output timestamps are aligned (within 60s)",
                    False,
                    f"Could not parse timestamps from {input_files[0].name} / {output_files[0].name}"
                )
        except Exception as e:
            add_check("Input and output timestamps are aligned (within 60s)", False, str(e))
    else:
        add_check(
            "Input and output timestamps are aligned (within 60s)",
            False,
            "Missing input or output files"
        )

    # =========================================================
    # CHECK 9: Required directory structure created
    # =========================================================
    required_dirs = [
        ws / "PhenoSnap",
        ws / "artifacts" / "phenosnap_inputs",
        ws / "artifacts" / "phenosnap_outputs",
        ws / "resources",
        ws / "third_party",
    ]
    dirs_ok = all(d.exists() for d in required_dirs)
    add_check(
        "All required directories created",
        dirs_ok,
        f"Dirs status: { {str(d): d.exists() for d in required_dirs} }"
    )

    # =========================================================
    # SCORING
    # =========================================================
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks) if checks else 0.0
    overall_passed = score >= 0.80  # Must pass at least 80% of checks

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)