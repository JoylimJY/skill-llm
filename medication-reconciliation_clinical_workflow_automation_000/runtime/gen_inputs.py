#!/usr/bin/env python3
"""
Generate the sandbox workspace for the medication reconciliation task.
Creates realistic messy inputs, distractor files, and the actual problem input files.
"""
import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── 1. Create the actual scripts/ directory and main.py ──────────────────────

scripts_dir = os.path.join(WORKSPACE, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

main_py = '''#!/usr/bin/env python3
"""
Medication Reconciliation Script
Compares pre-admission medication lists with inpatient orders.
"""
import argparse
import json
import sys
from pathlib import Path

CRITICAL_CLASSES = {
    "anticoagulant":     ["warfarin", "heparin", "enoxaparin", "apixaban", "rivaroxaban", "dabigatran"],
    "hypoglycemic":      ["metformin", "insulin", "glipizide", "glyburide", "sitagliptin", "glargine"],
    "antihypertensive":  ["lisinopril", "amlodipine", "metoprolol", "losartan", "atenolol", "hydrochlorothiazide"],
    "antiepileptic":     ["levetiracetam", "phenytoin", "valproate", "carbamazepine", "lamotrigine", "topiramate"],
}

EXAMPLE_PRE = {
    "patient_id": "EX-001",
    "medications": [
        {"drug": "Aspirin",    "dose": "81mg",   "route": "PO", "frequency": "daily"},
        {"drug": "Metoprolol", "dose": "50mg",   "route": "PO", "frequency": "BID"},
        {"drug": "Warfarin",   "dose": "5mg",    "route": "PO", "frequency": "daily"},
    ]
}
EXAMPLE_IN = {
    "patient_id": "EX-001",
    "orders": [
        {"drug": "Aspirin",    "dose": "81mg",   "route": "PO", "frequency": "daily"},
        {"drug": "Metoprolol", "dose": "100mg",  "route": "PO", "frequency": "BID"},
        {"drug": "Heparin",    "dose": "5000units", "route": "SC", "frequency": "TID"},
    ]
}


def normalize(name: str) -> str:
    return name.strip().lower()


def get_critical_warnings(drug_name: str) -> list[str]:
    n = normalize(drug_name)
    warnings = []
    for cls, drugs in CRITICAL_CLASSES.items():
        if n in drugs:
            warnings.append(f"{drug_name} is a {cls} — verify continuation/omission with clinical team.")
    return warnings


def reconcile(pre_list: list[dict], in_list: list[dict]) -> dict:
    report = {
        "continued":       [],
        "dose_changed":    [],
        "discontinued":    [],
        "new_medications": [],
        "duplicates":      [],
        "warnings":        [],
    }

    # Detect duplicates within each list
    def find_dupes(lst, key="drug"):
        seen = {}
        dupes = []
        for item in lst:
            k = normalize(item[key])
            seen.setdefault(k, []).append(item)
        for k, items in seen.items():
            if len(items) > 1:
                dupes.extend(items)
        return dupes

    pre_dupes = find_dupes(pre_list)
    in_dupes  = find_dupes(in_list)
    report["duplicates"] = pre_dupes + in_dupes

    # Build lookup by normalized drug name
    pre_map = {}
    for m in pre_list:
        pre_map.setdefault(normalize(m["drug"]), []).append(m)

    in_map = {}
    for o in in_list:
        in_map.setdefault(normalize(o["drug"]), []).append(o)

    all_drugs = set(pre_map.keys()) | set(in_map.keys())

    for drug_key in sorted(all_drugs):
        pre_entries = pre_map.get(drug_key)
        in_entries  = in_map.get(drug_key)

        if pre_entries and in_entries:
            pre_dose = pre_entries[0].get("dose", "")
            in_dose  = in_entries[0].get("dose", "")
            drug_display = pre_entries[0]["drug"]
            if pre_dose.strip().lower() == in_dose.strip().lower():
                entry = {"drug": drug_display, "dose": pre_dose}
                report["continued"].append(entry)
                for w in get_critical_warnings(drug_display):
                    report["warnings"].append(w)
            else:
                entry = {
                    "drug": drug_display,
                    "pre_admission_dose": pre_dose,
                    "inpatient_dose": in_dose,
                    "warning": "Dose change detected — verify with prescribing physician before proceeding."
                }
                report["dose_changed"].append(entry)
                for w in get_critical_warnings(drug_display):
                    report["warnings"].append(w)
        elif pre_entries and not in_entries:
            drug_display = pre_entries[0]["drug"]
            entry = {"drug": drug_display, "dose": pre_entries[0].get("dose", "")}
            report["discontinued"].append(entry)
            for w in get_critical_warnings(drug_display):
                report["warnings"].append(
                    f"{drug_display} was DISCONTINUED — verify intentional omission."
                )
        elif in_entries and not pre_entries:
            drug_display = in_entries[0]["drug"]
            entry = {"drug": drug_display, "dose": in_entries[0].get("dose", "")}
            report["new_medications"].append(entry)
            for w in get_critical_warnings(drug_display):
                report["warnings"].append(
                    f"{drug_display} is a new inpatient order ({', '.join([c for c, ds in CRITICAL_CLASSES.items() if normalize(drug_display) in ds])}) — verify with clinical team."
                )

    return report


def load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Medication Reconciliation Tool"
    )
    parser.add_argument("--pre-admission", dest="pre_admission", help="JSON file of pre-admission medications")
    parser.add_argument("--inpatient",     dest="inpatient",     help="JSON file of inpatient orders")
    parser.add_argument("--output",        dest="output",        help="Output report path (default: stdout)")
    parser.add_argument("--example",       action="store_true",  help="Run with built-in example data")
    parser.add_argument("--verbose",       action="store_true",  help="Include detailed matching rationale")
    args = parser.parse_args()

    if args.example:
        pre_data = EXAMPLE_PRE
        in_data  = EXAMPLE_IN
    else:
        if not args.pre_admission or not args.inpatient:
            print("ERROR: --pre-admission and --inpatient are required unless --example is used.", file=sys.stderr)
            sys.exit(1)
        pre_data = load_json(args.pre_admission)
        in_data  = load_json(args.inpatient)

    # Validate patient ID match
    pre_pid = pre_data.get("patient_id", "")
    in_pid  = in_data.get("patient_id",  "")
    if pre_pid != in_pid:
        print(f"ERROR: Patient ID mismatch — pre-admission: {pre_pid!r}, inpatient: {in_pid!r}", file=sys.stderr)
        sys.exit(2)

    pre_list = pre_data.get("medications", [])
    in_list  = in_data.get("orders",       [])

    if not pre_list:
        print("ERROR: Missing field 'medications' in pre-admission file.", file=sys.stderr)
        sys.exit(3)
    if not in_list:
        print("ERROR: Missing field 'orders' in inpatient file.", file=sys.stderr)
        sys.exit(3)

    report = reconcile(pre_list, in_list)

    output = {
        "patient_id":      pre_pid,
        "reconciliation":  report,
    }

    if args.verbose:
        output["matching_rationale"] = {
            "method": "Exact drug name normalization (case-insensitive, whitespace-stripped)",
            "dose_comparison": "Exact string match after strip()",
            "critical_class_check": list(CRITICAL_CLASSES.keys()),
        }

    result_str = json.dumps(output, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result_str)
        print(f"Report written to: {args.output}")
    else:
        print(result_str)


if __name__ == "__main__":
    main()
'''

with open(os.path.join(scripts_dir, "main.py"), "w") as f:
    f.write(main_py)

os.chmod(os.path.join(scripts_dir, "main.py"), 0o755)

# ── 2. Create the problem input files ────────────────────────────────────────

patient_pre_dir = os.path.join(WORKSPACE, "patient_data", "pre_admission")
patient_in_dir  = os.path.join(WORKSPACE, "patient_data", "inpatient")
os.makedirs(patient_pre_dir, exist_ok=True)
os.makedirs(patient_in_dir,  exist_ok=True)

# Pre-admission list for patient PT-00142
pre_admission_data = {
    "patient_id": "PT-00142",
    "encounter": "2024-11-15-ADMISSION",
    "medications": [
        {"drug": "Warfarin",      "dose": "5mg",    "route": "PO",  "frequency": "daily",   "indication": "DVT prophylaxis"},
        {"drug": "Metformin",     "dose": "500mg",  "route": "PO",  "frequency": "BID",     "indication": "Type 2 diabetes"},
        {"drug": "Lisinopril",    "dose": "10mg",   "route": "PO",  "frequency": "daily",   "indication": "Hypertension"},
        {"drug": "Levetiracetam", "dose": "500mg",  "route": "PO",  "frequency": "BID",     "indication": "Epilepsy"},
        {"drug": "Omeprazole",    "dose": "20mg",   "route": "PO",  "frequency": "daily",   "indication": "GERD"},
    ]
}

# Inpatient orders for patient PT-00142
inpatient_data = {
    "patient_id": "PT-00142",
    "admission_date": "2024-11-15",
    "ward": "Cardiology-4B",
    "orders": [
        {"drug": "Warfarin",      "dose": "5mg",    "route": "PO",  "frequency": "daily",   "ordered_by": "Dr. Patel"},
        {"drug": "Metformin",     "dose": "1000mg", "route": "PO",  "frequency": "BID",     "ordered_by": "Dr. Patel"},
        {"drug": "Levetiracetam", "dose": "500mg",  "route": "PO",  "frequency": "BID",     "ordered_by": "Dr. Nguyen"},
        {"drug": "Heparin",       "dose": "5000units", "route": "SC", "frequency": "TID",   "ordered_by": "Dr. Patel"},
        {"drug": "Pantoprazole",  "dose": "40mg",   "route": "IV",  "frequency": "daily",   "ordered_by": "Dr. Patel"},
    ]
}

with open(os.path.join(patient_pre_dir, "pt_00142_pre_meds.json"), "w") as f:
    json.dump(pre_admission_data, f, indent=2)

with open(os.path.join(patient_in_dir, "pt_00142_orders.json"), "w") as f:
    json.dump(inpatient_data, f, indent=2)

# ── 3. Distractor files ───────────────────────────────────────────────────────

# Old / archived data (wrong patient, wrong format, incomplete)
archive_dir = os.path.join(WORKSPACE, "patient_data", "archive")
os.makedirs(archive_dir, exist_ok=True)

old_data = {
    "patient_id": "PT-00099",
    "medications": [
        {"drug": "Atorvastatin", "dose": "40mg", "frequency": "nightly"},
    ]
}
with open(os.path.join(archive_dir, "pt_00099_old_meds.json"), "w") as f:
    json.dump(old_data, f, indent=2)

# A broken/incomplete JSON file to act as a trap
with open(os.path.join(archive_dir, "corrupted_orders.json"), "w") as f:
    f.write('{"patient_id": "PT-00142", "orders": [{"drug": "Aspirin"')  # intentionally truncated

# A CSV distractor
with open(os.path.join(archive_dir, "discharge_summary_PT00088.csv"), "w") as f:
    f.write("drug,dose,route\nLisinopril,5mg,PO\nAspirin,81mg,PO\n")

# Config/infra distractors
config_dir = os.path.join(WORKSPACE, "config")
os.makedirs(config_dir, exist_ok=True)

with open(os.path.join(config_dir, "app_config.yaml"), "w") as f:
    f.write("environment: production\nlog_level: INFO\ndb_host: localhost\ndb_port: 5432\n")

with open(os.path.join(config_dir, "drug_classes.yaml"), "w") as f:
    f.write(
        "# Outdated drug class config — do not use\n"
        "classes:\n"
        "  - anticoagulant\n"
        "  - antihypertensive\n"
    )

# Logs directory with noise
logs_dir = os.path.join(WORKSPACE, "logs")
os.makedirs(logs_dir, exist_ok=True)

with open(os.path.join(logs_dir, "reconciliation_2024-10-01.log"), "w") as f:
    f.write("[INFO] Run completed for PT-00130\n[WARN] Dose mismatch detected for Metoprolol\n")

with open(os.path.join(logs_dir, "reconciliation_2024-10-15.log"), "w") as f:
    f.write("[INFO] Run completed for PT-00137\n[INFO] No issues found\n")

with open(os.path.join(logs_dir, "error_2024-11-01.log"), "w") as f:
    f.write("[ERROR] Patient ID mismatch on intake PT-00141\n")

# Old reports that look like valid output but are for the WRONG patient
old_reports_dir = os.path.join(WORKSPACE, "reports", "completed")
os.makedirs(old_reports_dir, exist_ok=True)

old_report = {
    "patient_id": "PT-00130",
    "reconciliation": {
        "continued":       [{"drug": "Amlodipine", "dose": "5mg"}],
        "dose_changed":    [],
        "discontinued":    [{"drug": "Metoprolol", "dose": "50mg"}],
        "new_medications": [{"drug": "Carvedilol",  "dose": "6.25mg"}],
        "duplicates":      [],
        "warnings":        ["Amlodipine is an antihypertensive — verify continuation/omission with clinical team."]
    }
}
with open(os.path.join(old_reports_dir, "PT-00130_reconciliation.json"), "w") as f:
    json.dump(old_report, f, indent=2)

# Temp directory with partial/stale output
tmp_dir = os.path.join(WORKSPACE, "tmp")
os.makedirs(tmp_dir, exist_ok=True)

with open(os.path.join(tmp_dir, "staging_PT00142.json"), "w") as f:
    # Intentionally wrong/incomplete — a trap for agents that copy instead of running the script
    json.dump({
        "patient_id": "PT-00142",
        "reconciliation": {
            "continued": [{"drug": "Metformin", "dose": "500mg"}],  # WRONG: dose changed
            "discontinued": [],
            "new_medications": [],
            "duplicates": [],
            "warnings": []
        }
    }, f, indent=2)

# Test fixtures that look like valid pre/in files but are for different encounters
fixtures_dir = os.path.join(WORKSPACE, "tests", "fixtures")
os.makedirs(fixtures_dir, exist_ok=True)

with open(os.path.join(fixtures_dir, "sample_pre_meds.json"), "w") as f:
    json.dump({
        "patient_id": "TEST-001",
        "medications": [
            {"drug": "Aspirin", "dose": "81mg", "route": "PO", "frequency": "daily"}
        ]
    }, f, indent=2)

with open(os.path.join(fixtures_dir, "sample_orders.json"), "w") as f:
    json.dump({
        "patient_id": "TEST-001",
        "orders": [
            {"drug": "Aspirin", "dose": "81mg", "route": "PO", "frequency": "daily"},
            {"drug": "Ibuprofen", "dose": "400mg", "route": "PO", "frequency": "TID"}
        ]
    }, f, indent=2)

# Misc clinical docs
misc_dir = os.path.join(WORKSPACE, "docs", "clinical")
os.makedirs(misc_dir, exist_ok=True)

with open(os.path.join(misc_dir, "protocol_v2.txt"), "w") as f:
    f.write(
        "Medication Reconciliation Protocol v2\n"
        "======================================\n"
        "1. Collect pre-admission list from patient/GP.\n"
        "2. Cross-check with inpatient orders.\n"
        "3. Flag discrepancies for pharmacist review.\n"
        "NOTE: This is an outdated manual protocol. Use automated tooling where available.\n"
    )

with open(os.path.join(misc_dir, "formulary_2024Q3.txt"), "w") as f:
    f.write("Formulary listing for Q3 2024\n...see pharmacy department for details...\n")

print("Workspace generation complete.")
print("Key files:")
print(f"  Pre-admission: patient_data/pre_admission/pt_00142_pre_meds.json")
print(f"  Inpatient:     patient_data/inpatient/pt_00142_orders.json")
print(f"  Script:        scripts/main.py")