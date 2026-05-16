import os
import random
import csv
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ── Skill directory structure ──────────────────────────────────────────────────
skill_root = WORKSPACE / "skills" / "csv-cleanroom"
scripts_dir = skill_root / "scripts"
resources_dir = skill_root / "resources"
scripts_dir.mkdir(parents=True, exist_ok=True)
resources_dir.mkdir(parents=True, exist_ok=True)

# ── Bundled script: csv_cleanroom.py ──────────────────────────────────────────
csv_cleanroom_script = r'''#!/usr/bin/env python3
"""
csv_cleanroom.py  –  CSV Cleanroom v1.1.0
Usage:
    python3 csv_cleanroom.py profile   <input.csv>  [--out-dir DIR]
    python3 csv_cleanroom.py normalize <input.csv>  --schema SCHEMA_JSON [--out-dir DIR]
    python3 csv_cleanroom.py plan      <input.csv>  --schema SCHEMA_JSON [--out-dir DIR]
    python3 csv_cleanroom.py scorecard <input.csv>  --schema SCHEMA_JSON [--out-dir DIR]
    python3 csv_cleanroom.py all       <input.csv>  --schema SCHEMA_JSON [--out-dir DIR]

Commands:
    profile    – Produce profile_report.json   (row count, nulls, dupes, type mismatches, outliers)
    normalize  – Produce normalized_schema.json (header mapping to target schema)
    plan       – Produce cleanup_plan.json      (ordered remediation steps, preview/simulation only)
    scorecard  – Produce quality_scorecard.json (numeric quality score 0-100, per-dimension scores)
    all        – Run all four steps in order

Options:
    --schema   Path to target schema JSON  (required for normalize / plan / scorecard / all)
    --out-dir  Output directory            (default: current working directory)
"""

import sys, json, csv, re, os, argparse, collections, datetime
from pathlib import Path

# ── helpers ────────────────────────────────────────────────────────────────────

def slugify(s):
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")

def infer_type(values):
    non_null = [v for v in values if v not in ("", None, "NULL", "N/A", "n/a", "NA", "null", "none", "None")]
    if not non_null:
        return "empty"
    int_ok = all(re.fullmatch(r"-?\d+", v) for v in non_null)
    if int_ok:
        return "integer"
    float_ok = all(re.fullmatch(r"-?\d+(\.\d+)?", v) for v in non_null)
    if float_ok:
        return "float"
    date_patterns = [
        r"\d{4}-\d{2}-\d{2}", r"\d{2}/\d{2}/\d{4}", r"\d{2}-\d{2}-\d{4}",
        r"\d{4}/\d{2}/\d{2}",
    ]
    if all(any(re.fullmatch(p, v) for p in date_patterns) for v in non_null):
        return "date"
    currency_ok = all(re.fullmatch(r"[\$€£¥]?\s*-?\d[\d,]*(\.\d+)?", v) for v in non_null)
    if currency_ok:
        return "currency"
    return "string"

NULL_SENTINELS = {"", "NULL", "N/A", "n/a", "NA", "null", "none", "None", "-", "?"}

def is_null(v):
    return v.strip() in NULL_SENTINELS

def load_csv(path):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []
    return headers, rows

# ── commands ───────────────────────────────────────────────────────────────────

def cmd_profile(input_csv, out_dir):
    headers, rows = load_csv(input_csv)
    total_rows = len(rows)

    # duplicates: full-row equality
    row_tuples = [tuple(r.get(h, "") for h in headers) for r in rows]
    dup_count = total_rows - len(set(row_tuples))

    col_stats = {}
    for h in headers:
        vals = [r.get(h, "") for r in rows]
        null_count = sum(1 for v in vals if is_null(v))
        unique_count = len(set(v for v in vals if not is_null(v)))
        inferred = infer_type([v for v in vals if not is_null(v)])

        # outlier detection for numeric cols
        outliers = []
        if inferred in ("integer", "float"):
            nums = []
            for v in vals:
                if not is_null(v):
                    try:
                        nums.append(float(v))
                    except ValueError:
                        pass
            if len(nums) > 3:
                mean = sum(nums) / len(nums)
                std = (sum((x - mean) ** 2 for x in nums) / len(nums)) ** 0.5
                if std > 0:
                    outliers = [v for v in nums if abs(v - mean) > 3 * std]

        col_stats[h] = {
            "null_count": null_count,
            "null_pct": round(null_count / total_rows * 100, 2) if total_rows else 0,
            "unique_non_null": unique_count,
            "inferred_type": inferred,
            "outlier_count": len(outliers),
        }

    # type mismatches: mixed inferred types within a column (string catch-all ignored)
    type_mismatches = []
    for h, stats in col_stats.items():
        vals = [r.get(h, "") for r in rows if not is_null(r.get(h, ""))]
        if stats["inferred_type"] in ("integer", "float", "date"):
            bad = []
            for v in vals:
                if stats["inferred_type"] == "integer" and not re.fullmatch(r"-?\d+", v):
                    bad.append(v)
                elif stats["inferred_type"] == "float" and not re.fullmatch(r"-?\d+(\.\d+)?", v):
                    bad.append(v)
                elif stats["inferred_type"] == "date":
                    date_patterns = [
                        r"\d{4}-\d{2}-\d{2}", r"\d{2}/\d{2}/\d{4}",
                        r"\d{2}-\d{2}-\d{4}", r"\d{4}/\d{2}/\d{2}",
                    ]
                    if not any(re.fullmatch(p, v) for p in date_patterns):
                        bad.append(v)
            if bad:
                type_mismatches.append({"column": h, "inferred_type": stats["inferred_type"], "bad_samples": bad[:5]})

    report = {
        "input_file": str(input_csv),
        "total_rows": total_rows,
        "total_columns": len(headers),
        "duplicate_rows": dup_count,
        "columns": col_stats,
        "type_mismatches": type_mismatches,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    }
    out_path = Path(out_dir) / "profile_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"[profile] Written → {out_path}")
    return report

def cmd_normalize(input_csv, schema_path, out_dir):
    headers, _ = load_csv(input_csv)
    with open(schema_path) as f:
        target = json.load(f)
    target_fields = target.get("fields", [])
    target_slugs = {slugify(fld["name"]): fld["name"] for fld in target_fields}

    mapping = {}
    unmapped = []
    for h in headers:
        slug = slugify(h)
        if slug in target_slugs:
            mapping[h] = target_slugs[slug]
        else:
            # fuzzy: try substring match
            matched = None
            for ts, tname in target_slugs.items():
                if slug in ts or ts in slug:
                    matched = tname
                    break
            if matched:
                mapping[h] = matched
            else:
                mapping[h] = None
                unmapped.append(h)

    result = {
        "source_headers": headers,
        "header_mapping": mapping,
        "unmapped_columns": unmapped,
        "target_schema": target_fields,
    }
    out_path = Path(out_dir) / "normalized_schema.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"[normalize] Written → {out_path}")
    return result

def cmd_plan(input_csv, schema_path, out_dir, profile=None):
    if profile is None:
        headers, rows = load_csv(input_csv)
    else:
        headers = list(profile["columns"].keys())

    with open(schema_path) as f:
        target = json.load(f)

    steps = []
    step_num = 1

    steps.append({
        "step": step_num, "action": "PREVIEW",
        "description": "Simulation mode – no file will be modified until user confirms.",
        "reversible": True, "risk": "none",
    })
    step_num += 1

    if profile:
        if profile["duplicate_rows"] > 0:
            steps.append({
                "step": step_num, "action": "DEDUPLICATE",
                "description": f"Remove {profile['duplicate_rows']} exact duplicate rows.",
                "reversible": False, "risk": "medium",
            })
            step_num += 1

        for col, stats in profile["columns"].items():
            if stats["null_pct"] > 50:
                steps.append({
                    "step": step_num, "action": "DROP_COLUMN",
                    "description": f"Drop column '{col}' – {stats['null_pct']}% null (exceeds 50% threshold).",
                    "reversible": False, "risk": "high",
                })
                step_num += 1
            elif stats["null_count"] > 0:
                steps.append({
                    "step": step_num, "action": "FILL_NULLS",
                    "description": f"Fill {stats['null_count']} nulls in '{col}' with sentinel or imputed value.",
                    "reversible": False, "risk": "low",
                })
                step_num += 1

        for mismatch in profile.get("type_mismatches", []):
            steps.append({
                "step": step_num, "action": "TYPE_COERCE",
                "description": f"Coerce '{mismatch['column']}' to {mismatch['inferred_type']}; bad samples: {mismatch['bad_samples']}",
                "reversible": False, "risk": "medium",
            })
            step_num += 1

    steps.append({
        "step": step_num, "action": "NORMALIZE_HEADERS",
        "description": "Rename all columns to match target schema (slugified mapping).",
        "reversible": True, "risk": "low",
    })
    step_num += 1

    steps.append({
        "step": step_num, "action": "VALIDATE",
        "description": "Re-profile cleaned output against target schema to confirm compliance.",
        "reversible": True, "risk": "none",
    })

    plan = {
        "input_file": str(input_csv),
        "mode": "simulation",
        "note": "All irreversible operations documented above with risk level. No data modified.",
        "steps": steps,
    }
    out_path = Path(out_dir) / "cleanup_plan.json"
    out_path.write_text(json.dumps(plan, indent=2))
    print(f"[plan] Written → {out_path}")
    return plan

def cmd_scorecard(input_csv, schema_path, out_dir, profile=None):
    if profile is None:
        headers, rows = load_csv(input_csv)
        total_rows = len(rows)
    else:
        total_rows = profile["total_rows"]

    with open(schema_path) as f:
        target = json.load(f)

    if profile is None:
        _, rows = load_csv(input_csv)
        headers_local, _ = load_csv(input_csv)

    # Completeness: avg non-null %
    if profile:
        avg_non_null = 100 - (
            sum(s["null_pct"] for s in profile["columns"].values()) / max(len(profile["columns"]), 1)
        )
        dup_penalty = min(profile["duplicate_rows"] / max(total_rows, 1) * 100, 30)
        mismatch_penalty = len(profile.get("type_mismatches", [])) * 5
        outlier_penalty = sum(s["outlier_count"] for s in profile["columns"].values()) * 2
    else:
        avg_non_null = 70
        dup_penalty = 0
        mismatch_penalty = 0
        outlier_penalty = 0

    completeness = min(max(avg_non_null, 0), 100)
    uniqueness   = min(max(100 - dup_penalty, 0), 100)
    consistency  = min(max(100 - mismatch_penalty, 0), 100)
    validity     = min(max(100 - outlier_penalty, 0), 100)

    overall = round((completeness * 0.35 + uniqueness * 0.25 + consistency * 0.25 + validity * 0.15), 2)

    scorecard = {
        "input_file": str(input_csv),
        "dimensions": {
            "completeness": round(completeness, 2),
            "uniqueness":   round(uniqueness, 2),
            "consistency":  round(consistency, 2),
            "validity":     round(validity, 2),
        },
        "overall_quality_score": overall,
        "scale": "0-100",
        "remediation_checklist": [
            {"item": "Fix all null values above 10% threshold", "priority": "HIGH"},
            {"item": "Remove or merge exact duplicate rows",    "priority": "HIGH"},
            {"item": "Coerce columns to declared schema types", "priority": "MEDIUM"},
            {"item": "Cap or investigate statistical outliers", "priority": "MEDIUM"},
            {"item": "Rename headers to match target schema",   "priority": "LOW"},
        ],
    }
    out_path = Path(out_dir) / "quality_scorecard.json"
    out_path.write_text(json.dumps(scorecard, indent=2))
    print(f"[scorecard] Written → {out_path}")
    return scorecard

def cmd_all(input_csv, schema_path, out_dir):
    profile  = cmd_profile(input_csv, out_dir)
    _norm    = cmd_normalize(input_csv, schema_path, out_dir)
    _plan    = cmd_plan(input_csv, schema_path, out_dir, profile=profile)
    _score   = cmd_scorecard(input_csv, schema_path, out_dir, profile=profile)
    print("[all] Done – four artifacts written.")

# ── main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CSV Cleanroom v1.1.0")
    parser.add_argument("command", choices=["profile","normalize","plan","scorecard","all"])
    parser.add_argument("input_csv")
    parser.add_argument("--schema",  default=None)
    parser.add_argument("--out-dir", default=".")
    args = parser.parse_args()

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    if args.command == "profile":
        cmd_profile(args.input_csv, args.out_dir)
    elif args.command == "normalize":
        if not args.schema:
            print("ERROR: --schema required for normalize"); sys.exit(1)
        cmd_normalize(args.input_csv, args.schema, args.out_dir)
    elif args.command == "plan":
        if not args.schema:
            print("ERROR: --schema required for plan"); sys.exit(1)
        cmd_plan(args.input_csv, args.schema, args.out_dir)
    elif args.command == "scorecard":
        if not args.schema:
            print("ERROR: --schema required for scorecard"); sys.exit(1)
        cmd_scorecard(args.input_csv, args.schema, args.out_dir)
    elif args.command == "all":
        if not args.schema:
            print("ERROR: --schema required for all"); sys.exit(1)
        cmd_all(args.input_csv, args.schema, args.out_dir)

if __name__ == "__main__":
    main()
'''

(scripts_dir / "csv_cleanroom.py").write_text(csv_cleanroom_script)

# ── Bundled resource: data_quality_checklist.md ───────────────────────────────
checklist_md = """\
# Data Quality Checklist — CSV Cleanroom v1.1.0

## Default Target Schema

```json
{
  "fields": [
    {"name": "supplier_id",    "type": "string",  "required": true},
    {"name": "supplier_name",  "type": "string",  "required": true},
    {"name": "invoice_number", "type": "string",  "required": true},
    {"name": "invoice_date",   "type": "date",    "required": true,  "format": "YYYY-MM-DD"},
    {"name": "amount_usd",     "type": "currency","required": true},
    {"name": "payment_status", "type": "string",  "required": false},
    {"name": "region",         "type": "string",  "required": false}
  ]
}
```

## Quality Dimensions

| Dimension    | Weight | Description                                      |
|--------------|--------|--------------------------------------------------|
| Completeness | 35%    | Non-null rate across required fields             |
| Uniqueness   | 25%    | Absence of exact duplicate rows                  |
| Consistency  | 25%    | Type conformance to declared schema              |
| Validity     | 15%    | Absence of statistical outliers in numeric cols  |

## Remediation Checklist

- [ ] All required fields populated
- [ ] Zero exact duplicate rows
- [ ] Dates in ISO 8601 (YYYY-MM-DD) format
- [ ] Amounts parseable as numeric (strip currency symbols)
- [ ] Column names match target schema (case-insensitive, snake_case)

## Risk Classifications

- `none`   – Read-only / preview operations
- `low`    – Reversible transformations (renames, fills with sentinel)
- `medium` – Potentially lossy (deduplication, type coercion)
- `high`   – Destructive / irreversible (column drops)
"""
(resources_dir / "data_quality_checklist.md").write_text(checklist_md)

# ── Task input data: messy supplier CSV ───────────────────────────────────────
data_dir = WORKSPACE / "data" / "procurement" / "q2_2024"
data_dir.mkdir(parents=True, exist_ok=True)

# Messy CSV with: wrong/inconsistent headers, mixed date formats, duplicate rows,
# null sentinels, currency symbols, a column with >50% nulls, type mismatches
messy_csv_rows = [
    # Header row – inconsistent naming (spaces, CamelCase, abbreviations)
    ["Supplier ID", "SupplierName", "Inv#", "Invoice Date", "Amt (USD)", "Pay Status", "Region", "Notes"],
    # Good rows
    ["S001", "Acme Corp",      "INV-001", "2024-01-15", "$1200.00",  "PAID",    "APAC",   "OK"],
    ["S002", "Globex Ltd",     "INV-002", "2024-01-18", "$850.50",   "PENDING", "EMEA",   "N/A"],
    ["S003", "Initech LLC",    "INV-003", "15/02/2024", "$3400.00",  "PAID",    "AMER",   ""],
    # Duplicate of row index 1
    ["S001", "Acme Corp",      "INV-001", "2024-01-15", "$1200.00",  "PAID",    "APAC",   "OK"],
    # Null sentinels in required fields
    ["S004", "Umbrella Inc",   "INV-004", "NULL",        "$975.00",  "PAID",    "APAC",   ""],
    ["S005", "N/A",            "INV-005", "2024-02-20", "$2200.00",  "PENDING", "AMER",   ""],
    # Amount with missing currency – type mismatch (letters mixed in)
    ["S006", "Massive Dyn",    "INV-006", "2024-03-01", "TBD",       "PENDING", "EMEA",   ""],
    # Notes column >50% null (already seeded as N/A or blank above – let's ensure)
    ["S007", "Soylent Corp",   "INV-007", "2024-03-05", "$445.00",   "PAID",    "APAC",   ""],
    ["S008", "Rekall Inc",     "INV-008", "2024/03/10", "$12000.00", "PAID",    "AMER",   ""],
    ["S009", "Tyrell Corp",    "INV-009", "2024-03-12", "$780.25",   "PENDING", "EMEA",   ""],
    # Outlier in amount
    ["S010", "Omni Consumer",  "INV-010", "2024-03-15", "$999999.99","PAID",    "APAC",   ""],
    ["S011", "Weyland Corp",   "INV-011", "2024-03-18", "$1100.00",  "PAID",    "EMEA",   ""],
    ["S012", "Delos Inc",      "INV-012", "2024-03-20", "none",      "PENDING", "AMER",   ""],
    # Another duplicate
    ["S003", "Initech LLC",    "INV-003", "15/02/2024", "$3400.00",  "PAID",    "AMER",   ""],
]

import csv as _csv
with open(data_dir / "supplier_invoices_q2_2024.csv", "w", newline="", encoding="utf-8") as f:
    writer = _csv.writer(f)
    writer.writerows(messy_csv_rows)

# ── Distractor files ───────────────────────────────────────────────────────────
distractors = WORKSPACE / "distractors"

# 1. Old backup CSV (different schema, not the target)
old_dir = distractors / "archive" / "2023"
old_dir.mkdir(parents=True, exist_ok=True)
with open(old_dir / "invoices_2023_backup.csv", "w", newline="") as f:
    w = _csv.writer(f)
    w.writerows([["id","name","date","total"],["1","OldCorp","2023-01-01","500"]])

# 2. Unrelated JSON config
import os as _os
_os.makedirs(str(distractors / "config"), exist_ok=True)
(distractors / "config" / "pipeline.json").write_text(json.dumps({"version": "2.0", "steps": ["ingest","transform","load"]}))

# 3. A README-like file that gives NO hints
(distractors / "config" / "NOTES.txt").write_text("Internal notes – pipeline v2 migration in progress. Contact DevOps for questions.\n")

# 4. Stale schema file (wrong format, not the checklist)
_os.makedirs(str(distractors / "schemas"), exist_ok=True)
(distractors / "schemas" / "old_schema_v0.json").write_text(json.dumps({"columns": ["id","vendor","date","value"]}))

# 5. Empty placeholder CSV
_os.makedirs(str(distractors / "staging"), exist_ok=True)
(distractors / "staging" / "placeholder.csv").write_text("col1,col2,col3\n")

# 6. Log file from a previous (unrelated) run
_os.makedirs(str(distractors / "logs"), exist_ok=True)
(distractors / "logs" / "etl_run_20240101.log").write_text("[INFO] 2024-01-01 pipeline started\n[INFO] processed 0 rows\n[INFO] done\n")

# 7. Python utility (unrelated)
_os.makedirs(str(distractors / "utils"), exist_ok=True)
(distractors / "utils" / "db_connect.py").write_text("# placeholder – DB connector not in scope\n")

# 8. Another messy CSV in staging (different domain – HR)
with open(distractors / "staging" / "hr_headcount.csv", "w", newline="") as f:
    w = _csv.writer(f)
    w.writerows([["EmpID","First Name","Last","Dept","Salary"],
                 ["E001","Alice","Smith","Eng","90000"],
                 ["E002","Bob","Jones","HR","NULL"]])

# 9. Stale requirements file
(distractors / "requirements_old.txt").write_text("pandas==1.3.0\nnumpy==1.21.0\n")

# 10. Nested dummy report (XML format, wrong tool)
_os.makedirs(str(distractors / "reports" / "xml"), exist_ok=True)
(distractors / "reports" / "xml" / "legacy_report.xml").write_text(
    "<?xml version='1.0'?><report><rows>0</rows></report>\n"
)

print("Workspace generated successfully.")
print(f"Skill root : {skill_root}")
print(f"Messy CSV  : {data_dir / 'supplier_invoices_q2_2024.csv'}")