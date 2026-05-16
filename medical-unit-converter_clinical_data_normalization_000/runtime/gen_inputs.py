import os
import random
import csv

random.seed(42)

# ── create the workspace skeleton ──────────────────────────────────────────────
base = "/workspace"

dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/archive",
    "docs/protocols",
    "docs/references",
    "config",
    "logs",
    "reports/drafts",
    "reports/final",
    "tests",
    "notebooks",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────────
distractors = {
    "config/db_config.ini": "[database]\nhost=localhost\nport=5432\nname=clinical_db\nuser=readonly\n",
    "config/export_settings.yaml": "export:\n  format: csv\n  delimiter: comma\n  encoding: utf-8\n",
    "docs/protocols/sample_handling.txt": "All blood samples must be centrifuged within 30 minutes of collection.\nStore serum at -20C for long-term stability.\n",
    "docs/references/unit_notes.txt": "Legacy EHR exports values in conventional US units (mg/dL).\nEuropean partner sites use SI units (mmol/L).\nReconciliation required before database import.\n",
    "data/archive/cohort_2021_backup.csv": "patient_id,analyte,value,unit\n1001,glucose,95,mg/dL\n1002,cholesterol,210,mg/dL\n",
    "data/archive/mapping_table_old.csv": "old_code,new_code\nGLU,glucose\nCHOL,cholesterol\nCREAT,creatinine\nHGB,hemoglobin\n",
    "logs/etl_run_20240101.log": "[INFO] ETL started\n[INFO] 342 records loaded\n[WARN] 5 records skipped: unsupported analyte\n[INFO] ETL complete\n",
    "logs/etl_run_20240315.log": "[INFO] ETL started\n[ERROR] Unit mismatch on row 14\n[INFO] ETL aborted\n",
    "reports/drafts/conversion_summary_DRAFT.txt": "DRAFT - DO NOT USE\nThis file is a placeholder.\nConversion logic not yet finalized.\n",
    "tests/test_placeholder.py": "# TODO: add unit tests for conversion pipeline\ndef test_stub():\n    pass\n",
    "notebooks/exploratory_analysis.py": "# Quick exploration - not production code\nimport csv\nprint('placeholder notebook')\n",
    "data/processed/.gitkeep": "",
    "reports/final/.gitkeep": "",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(base, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── the actual skill: scripts/main.py ──────────────────────────────────────────
# This is the packaged script that the SKILL.md documents.
main_py = '''\
#!/usr/bin/env python3
"""Medical Unit Converter — packaged script."""

import argparse
import json
import sys

CONVERSIONS = {
    ("glucose", "mg_dl", "mmol_l"): {
        "factor": 0.0555,
        "reference_range": "3.9\\u20135.6 mmol/L (fasting glucose)",
    },
    ("glucose", "mmol_l", "mg_dl"): {
        "factor": 18.018,
        "reference_range": "70\\u2013100 mg/dL (fasting glucose)",
    },
    ("cholesterol", "mg_dl", "mmol_l"): {
        "factor": 0.02586,
        "reference_range": "< 5.2 mmol/L (desirable cholesterol)",
    },
    ("cholesterol", "mmol_l", "mg_dl"): {
        "factor": 38.67,
        "reference_range": "< 200 mg/dL (desirable cholesterol)",
    },
    ("creatinine", "mg_dl", "umol_l"): {
        "factor": 88.4,
        "reference_range": "62\\u2013115 \\u03bcmol/L (male creatinine)",
    },
    ("creatinine", "umol_l", "mg_dl"): {
        "factor": 0.01131,
        "reference_range": "0.7\\u20131.3 mg/dL (male creatinine)",
    },
    ("hemoglobin", "g_dl", "g_l"): {
        "factor": 10,
        "reference_range": "130\\u2013175 g/L (male hemoglobin)",
    },
    ("hemoglobin", "g_l", "g_dl"): {
        "factor": 0.1,
        "reference_range": "13\\u201317.5 g/dL (male hemoglobin)",
    },
}


class MedicalUnitConverter:
    def convert(self, value: float, from_unit: str, to_unit: str, analyte: str = None):
        key = (analyte, from_unit, to_unit) if analyte else None
        entry = CONVERSIONS.get(key) if key else None

        if entry is None:
            # Try without analyte hint
            if analyte is None:
                for (a, f, t), v in CONVERSIONS.items():
                    if f == from_unit and t == to_unit:
                        entry = v
                        analyte = a
                        break

        if entry is None:
            print("Unsupported conversion pair.")
            print("Supported conversions:")
            for (a, f, t) in CONVERSIONS:
                print(f"  {a}: {f} -> {t}")
            sys.exit(1)

        factor = entry["factor"]
        converted = round(value * factor, 4)
        return {
            "converted_value": converted,
            "formula": f"{value} \\u00d7 {factor}",
            "from_unit": from_unit,
            "to_unit": to_unit,
            "analyte": analyte,
            "reference_range": entry["reference_range"],
        }


def main():
    parser = argparse.ArgumentParser(description="Medical Unit Converter")
    parser.add_argument("--value", "-v", type=float, required=True)
    parser.add_argument("--from-unit", required=True)
    parser.add_argument("--to-unit", required=True)
    parser.add_argument("--analyte", "-a", default=None)
    args = parser.parse_args()

    conv = MedicalUnitConverter()
    result = conv.convert(
        value=args.value,
        from_unit=args.from_unit,
        to_unit=args.to_unit,
        analyte=args.analyte,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
'''

with open(os.path.join(base, "scripts/main.py"), "w") as f:
    f.write(main_py)

# ── the messy lab export CSV ──────────────────────────────────────────────────
# 8 rows: valid conversions + 1 unsupported analyte + 1 duplicate/edge case
lab_rows = [
    # patient_id, analyte, value, from_unit, to_unit, notes
    ["PT-001", "glucose",     "126",   "mg_dl",  "mmol_l", "fasting sample"],
    ["PT-002", "glucose",     "7.2",   "mmol_l", "mg_dl",  "post-meal unclear"],
    ["PT-003", "cholesterol", "215",   "mg_dl",  "mmol_l", "annual check"],
    ["PT-004", "cholesterol", "5.8",   "mmol_l", "mg_dl",  "follow-up"],
    ["PT-005", "creatinine",  "1.1",   "mg_dl",  "umol_l", "CKD monitoring"],
    ["PT-006", "creatinine",  "97.5",  "umol_l", "mg_dl",  "nephrology"],
    ["PT-007", "hemoglobin",  "14.5",  "g_dl",   "g_l",    "pre-op"],
    ["PT-008", "hemoglobin",  "155",   "g_l",    "g_dl",   "oncology"],
    # unsupported analyte — should trigger fallback
    ["PT-009", "tsh",         "3.4",   "miu_l",  "pmol_l", "thyroid panel"],
]

csv_path = os.path.join(base, "data/raw/lab_export_batch_Q1.csv")
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["patient_id", "analyte", "value", "from_unit", "to_unit", "notes"])
    writer.writerows(lab_rows)

print("Workspace generated successfully.")
print(f"Lab export CSV: {csv_path}")