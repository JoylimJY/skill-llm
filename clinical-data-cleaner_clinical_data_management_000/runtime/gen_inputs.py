import os
import json
import random
import pandas as pd
import numpy as np
from pathlib import Path

random.seed(42)
np.random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "raw_data",
    "archive/2022_submissions",
    "archive/2023_interim",
    "docs/protocol",
    "docs/sap",
    "logs",
    "temp_exports",
    "qc_checks",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────

# 1. Old DM domain file (not the target)
dm_old = pd.DataFrame({
    "STUDYID": ["ONCO-2023"] * 5,
    "USUBJID": [f"ONCO-2023-001-00{i}" for i in range(1, 6)],
    "SUBJID": [f"00{i}" for i in range(1, 6)],
    "RFSTDTC": ["2023-01-15"] * 5,
    "RFENDTC": ["2023-06-30"] * 5,
    "SITEID": ["001"] * 5,
    "AGE": [45, 52, 38, 61, 47],
    "SEX": ["M", "F", "M", "F", "M"],
    "RACE": ["WHITE"] * 5,
})
dm_old.to_csv(workspace / "archive/2023_interim/dm_interim.csv", index=False)

# 2. VS domain file (distractor)
vs_data = pd.DataFrame({
    "STUDYID": ["ONCO-2023"] * 8,
    "USUBJID": [f"ONCO-2023-001-00{i}" for i in range(1, 9)],
    "VSTESTCD": ["SYSBP", "DIABP", "PULSE", "SYSBP", "DIABP", "PULSE", "SYSBP", "DIABP"],
    "VSORRES": [120, 80, 72, 135, 85, 68, 118, 78],
    "VSORRESU": ["mmHg"] * 6 + ["mmHg"] * 2,
    "VSSTRESC": [120, 80, 72, 135, 85, 68, 118, 78],
    "VSDTC": ["2023-03-15T08:00:00"] * 8,
})
vs_data.to_csv(workspace / "archive/2023_interim/vs_interim.csv", index=False)

# 3. Protocol document (distractor text file)
with open(workspace / "docs/protocol/protocol_v3.txt", "w") as f:
    f.write("ONCO-2023 Protocol v3.0\nPhase III Oncology Trial\nData cutoff: 2024-03-31\n")

# 4. SAP document
with open(workspace / "docs/sap/statistical_analysis_plan.txt", "w") as f:
    f.write("SAP v2.1\nPrimary endpoint: Overall survival\nMissing data: Median imputation for continuous vars\n")

# 5. Old cleaning log
with open(workspace / "logs/cleaning_log_2023.txt", "w") as f:
    f.write("[2023-11-01] DM domain cleaned. 3 missing values imputed.\n[2023-11-02] VS domain cleaned. 0 outliers.\n")

# 6. Requirements file (distractor)
with open(workspace / "temp_exports/export_manifest.txt", "w") as f:
    f.write("Export date: 2024-03-31\nExported domains: DM, LB, VS, AE\nRecord counts: DM=127, LB=3840, VS=1270\n")

# 7. QC notes
with open(workspace / "qc_checks/qc_notes.txt", "w") as f:
    f.write("QC Note: LB data has non-standard column names from CRO export.\nAction required: Map to SDTM before submission.\n")

# 8. Old references JSON that is wrong (distractor)
with open(workspace / "archive/2022_submissions/old_thresholds.json", "w") as f:
    json.dump({"glucose_min": 40, "glucose_max": 600}, f)

# 9. Another distractor CSV
pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]}).to_csv(
    workspace / "temp_exports/raw_dump.csv", index=False
)

# 10. Empty placeholder
with open(workspace / "qc_checks/validation_results.txt", "w") as f:
    f.write("Pending validation...\n")

# ── The actual tool scripts (pre-exist in the workspace per skill rules) ──────
# scripts/main.py — the ClinicalDataCleaner implementation
main_py = '''#!/usr/bin/env python3
"""Clinical Data Cleaner - CDISC SDTM Standardization Tool v2.0"""

import argparse
import json
import re
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Domain specifications ─────────────────────────────────────────────────────
DOMAIN_REQUIRED_FIELDS = {
    "DM": ["STUDYID", "USUBJID", "SUBJID", "RFSTDTC", "RFENDTC", "SITEID", "AGE", "SEX", "RACE"],
    "LB": ["STUDYID", "USUBJID", "LBTESTCD", "LBCAT", "LBORRES", "LBORRESU", "LBSTRESC", "LBDTC"],
    "VS": ["STUDYID", "USUBJID", "VSTESTCD", "VSORRES", "VSORRESU", "VSSTRESC", "VSDTC"],
}

# Clinical outlier thresholds (domain method)
CLINICAL_THRESHOLDS = {
    "GLUCOSE": {"min": 50, "max": 500, "unit": "mg/dL"},
    "HGB":     {"min": 5,  "max": 20,  "unit": "g/dL"},
    "HEMOGLOBIN": {"min": 5, "max": 20, "unit": "g/dL"},
    "SYSBP":   {"min": 70, "max": 220, "unit": "mmHg"},
    "DIABP":   {"min": 40, "max": 130, "unit": "mmHg"},
    "PULSE":   {"min": 30, "max": 200, "unit": "bpm"},
    "TEMP":    {"min": 35, "max": 42,  "unit": "C"},
    "WBC":     {"min": 1,  "max": 100, "unit": "10^3/uL"},
    "PLT":     {"min": 10, "max": 1500,"unit": "10^3/uL"},
    "CREAT":   {"min": 0.3,"max": 15,  "unit": "mg/dL"},
    "ALT":     {"min": 1,  "max": 2000,"unit": "U/L"},
    "AST":     {"min": 1,  "max": 2000,"unit": "U/L"},
}

DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%b-%Y",
    "%Y%m%d",
    "%d.%m.%Y",
    "%m-%d-%Y",
    "%d/%m/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
]


class ClinicalDataCleaner:
    def __init__(
        self,
        domain: str = "DM",
        missing_strategy: str = "median",
        outlier_method: str = "iqr",
        outlier_action: str = "flag",
    ):
        self.domain = domain.upper()
        self.missing_strategy = missing_strategy
        self.outlier_method = outlier_method
        self.outlier_action = outlier_action
        self.audit_trail = []
        self._cleaned_data = None
        self._log(f"Initialized ClinicalDataCleaner: domain={domain}, "
                  f"missing_strategy={missing_strategy}, "
                  f"outlier_method={outlier_method}, "
                  f"outlier_action={outlier_action}")

    def _log(self, message: str, level: str = "INFO"):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message,
        }
        self.audit_trail.append(entry)

    # ── Validation ────────────────────────────────────────────────────────────
    def validate_domain(self, data: pd.DataFrame) -> Tuple[bool, list]:
        required = DOMAIN_REQUIRED_FIELDS.get(self.domain, [])
        missing = [f for f in required if f not in data.columns]
        is_valid = len(missing) == 0
        if missing:
            self._log(f"Validation failed. Missing required fields: {missing}", "WARNING")
        else:
            self._log("Domain validation passed.")
        return is_valid, missing

    # ── Missing values ────────────────────────────────────────────────────────
    def handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        strategy = self.missing_strategy
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        imputed_count = 0

        for col in numeric_cols:
            n_missing = df[col].isna().sum()
            if n_missing == 0:
                continue
            if strategy == "mean":
                fill_val = df[col].mean()
            elif strategy == "median":
                fill_val = df[col].median()
            elif strategy == "mode":
                fill_val = df[col].mode().iloc[0] if not df[col].mode().empty else np.nan
            elif strategy == "forward":
                df[col] = df[col].fillna(method="ffill")
                self._log(f"Forward-filled {n_missing} missing values in '{col}'")
                imputed_count += n_missing
                continue
            elif strategy == "drop":
                df = df.dropna(subset=[col])
                self._log(f"Dropped {n_missing} rows with missing '{col}'")
                continue
            else:
                fill_val = df[col].median()

            df[col] = df[col].fillna(fill_val)
            imputed_count += n_missing
            self._log(f"Imputed {n_missing} missing values in '{col}' using {strategy} (value={round(float(fill_val),4)})")

        # Also handle categorical columns with mode
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        for col in cat_cols:
            n_missing = df[col].isna().sum()
            if n_missing > 0:
                fill_val = df[col].mode().iloc[0] if not df[col].mode().empty else "UNKNOWN"
                df[col] = df[col].fillna(fill_val)
                imputed_count += n_missing
                self._log(f"Imputed {n_missing} missing categorical values in '{col}' with mode=\'{fill_val}\'")

        self._log(f"Missing value handling complete. Total imputed: {imputed_count}")
        return df

    # ── Outlier detection ─────────────────────────────────────────────────────
    def detect_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        method = self.outlier_method
        action = self.outlier_action
        outlier_count = 0

        if method == "domain":
            # Use clinical thresholds; requires LBTESTCD/VSTESTCD column
            test_col = None
            value_col = None
            if "LBTESTCD" in df.columns and "LBORRES" in df.columns:
                test_col, value_col = "LBTESTCD", "LBORRES"
            elif "VSTESTCD" in df.columns and "VSORRES" in df.columns:
                test_col, value_col = "VSTESTCD", "VSORRES"

            if test_col and value_col:
                df["OUTLIER_FL"] = ""
                for idx, row in df.iterrows():
                    testcd = str(row[test_col]).upper()
                    threshold = CLINICAL_THRESHOLDS.get(testcd)
                    if threshold is None:
                        continue
                    try:
                        val = float(row[value_col])
                    except (ValueError, TypeError):
                        continue
                    if val < threshold["min"] or val > threshold["max"]:
                        outlier_count += 1
                        if action == "flag":
                            df.at[idx, "OUTLIER_FL"] = "Y"
                            self._log(f"Outlier flagged: {test_col}={testcd}, "
                                      f"{value_col}={val} (range {threshold[\'min\']}-{threshold[\'max\']} {threshold[\'unit\']})")
                        elif action == "remove":
                            df = df.drop(idx)
                            self._log(f"Outlier removed: {test_col}={testcd}, {value_col}={val}")
                        elif action == "cap":
                            capped = max(threshold["min"], min(threshold["max"], val))
                            df.at[idx, value_col] = capped
                            df.at[idx, "OUTLIER_FL"] = "CAPPED"
                            self._log(f"Outlier capped: {test_col}={testcd}, {value_col} {val} -> {capped}")
            else:
                self._log("Domain method: no test code + value column pair found; skipping.", "WARNING")

        elif method in ("iqr", "zscore"):
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            for col in numeric_cols:
                series = df[col].dropna()
                if len(series) < 4:
                    continue
                if method == "iqr":
                    q1, q3 = series.quantile(0.25), series.quantile(0.75)
                    iqr = q3 - q1
                    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                else:  # zscore
                    mean, std = series.mean(), series.std()
                    lo, hi = mean - 3 * std, mean + 3 * std

                mask = (df[col] < lo) | (df[col] > hi)
                n_out = mask.sum()
                if n_out == 0:
                    continue
                outlier_count += n_out
                flag_col = f"{col}_OUTLIER"
                if action == "flag":
                    df[flag_col] = np.where(mask, "Y", "")
                    self._log(f"Flagged {n_out} outliers in \'{col}\' ({method})")
                elif action == "remove":
                    df = df[~mask]
                    self._log(f"Removed {n_out} outliers in \'{col}\' ({method})")
                elif action == "cap":
                    df[col] = df[col].clip(lower=lo, upper=hi)
                    self._log(f"Capped {n_out} outliers in \'{col}\' ({method})")

        self._log(f"Outlier detection complete. Total affected: {outlier_count} (method={method}, action={action})")
        return df

    # ── Date standardization ──────────────────────────────────────────────────
    def standardize_dates(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        date_cols = [c for c in df.columns if "DTC" in c or "DATE" in c.upper()]
        standardized_count = 0
        error_count = 0

        for col in date_cols:
            if col not in df.columns:
                continue
            converted = []
            for val in df[col]:
                if pd.isna(val) or val == "":
                    converted.append(val)
                    continue
                parsed = None
                for fmt in DATE_FORMATS:
                    try:
                        parsed = datetime.strptime(str(val).strip(), fmt)
                        break
                    except ValueError:
                        continue
                if parsed:
                    converted.append(parsed.strftime("%Y-%m-%dT%H:%M:%S"))
                    standardized_count += 1
                else:
                    converted.append(val)
                    error_count += 1
                    self._log(f"Could not parse date \'{val}\' in column \'{col}\'", "WARNING")
            df[col] = converted

        self._log(f"Date standardization complete. Standardized: {standardized_count}, Errors: {error_count}")
        return df

    # ── Full pipeline ─────────────────────────────────────────────────────────
    def clean(self, data: pd.DataFrame) -> pd.DataFrame:
        self._log(f"Starting clean pipeline. Input rows: {len(data)}, columns: {list(data.columns)}")

        is_valid, missing = self.validate_domain(data)
        if not is_valid:
            self._log(f"Proceeding with missing fields: {missing}", "WARNING")

        df = self.handle_missing_values(data)
        df = self.detect_outliers(df)
        df = self.standardize_dates(df)

        self._log(f"Clean pipeline complete. Output rows: {len(df)}, columns: {list(df.columns)}")
        self._cleaned_data = df
        return df

    # ── Save ──────────────────────────────────────────────────────────────────
    def save_report(self, output_path: str):
        base = output_path.replace(".csv", "")
        csv_path = base + ".csv"
        report_path = base + ".report.json"

        if self._cleaned_data is not None:
            self._cleaned_data.to_csv(csv_path, index=False)
            self._log(f"Cleaned data saved to {csv_path}")
        else:
            self._log("No cleaned data to save.", "WARNING")

        report = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "domain": self.domain,
            "missing_strategy": self.missing_strategy,
            "outlier_method": self.outlier_method,
            "outlier_action": self.outlier_action,
            "audit_trail": self.audit_trail,
            "record_count": len(self._cleaned_data) if self._cleaned_data is not None else 0,
        }
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        self._log(f"Audit report saved to {report_path}")

        return csv_path, report_path


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Clinical Data Cleaner v2.0")
    parser.add_argument("--input",            required=True)
    parser.add_argument("--domain",           required=True)
    parser.add_argument("--output",           required=True)
    parser.add_argument("--missing-strategy", default="median")
    parser.add_argument("--outlier-method",   default="iqr")
    parser.add_argument("--outlier-action",   default="flag")
    args = parser.parse_args()

    data = pd.read_csv(args.input)
    cleaner = ClinicalDataCleaner(
        domain=args.domain,
        missing_strategy=args.missing_strategy,
        outlier_method=args.outlier_method,
        outlier_action=args.outlier_action,
    )
    cleaned = cleaner.clean(data)
    cleaner.save_report(args.output)
    print(f"Done. Output: {args.output}")
    print(f"Records: {len(cleaned)}")


if __name__ == "__main__":
    main()
'''

(workspace / "scripts/main.py").write_text(main_py)

# ── References ───────────────────────────────────────────────────────────────
sdtm_guide = """# CDISC SDTM Implementation Guide (Excerpt)

## Domain Specifications

### DM - Demographics
Required variables: STUDYID, USUBJID, SUBJID, RFSTDTC, RFENDTC, SITEID, AGE, SEX, RACE

### LB - Laboratory Test Results
Required variables: STUDYID, USUBJID, LBTESTCD, LBCAT, LBORRES, LBORRESU, LBSTRESC, LBDTC
LBTESTCD: Short test code (e.g., GLUCOSE, HGB, WBC)
LBCAT: Category (e.g., HEMATOLOGY, CHEMISTRY)
LBORRES: Original result
LBORRESU: Original units
LBSTRESC: Standardized result (character)
LBDTC: Date/time of specimen collection

### VS - Vital Signs
Required variables: STUDYID, USUBJID, VSTESTCD, VSORRES, VSORRESU, VSSTRESC, VSDTC
"""
(workspace / "references/sdtm_ig_guide.md").write_text(sdtm_guide)

domain_specs = {
    "DM": {"required": ["STUDYID","USUBJID","SUBJID","RFSTDTC","RFENDTC","SITEID","AGE","SEX","RACE"]},
    "LB": {"required": ["STUDYID","USUBJID","LBTESTCD","LBCAT","LBORRES","LBORRESU","LBSTRESC","LBDTC"]},
    "VS": {"required": ["STUDYID","USUBJID","VSTESTCD","VSORRES","VSORRESU","VSSTRESC","VSDTC"]},
}
with open(workspace / "references/domain_specs.json", "w") as f:
    json.dump(domain_specs, f, indent=2)

outlier_thresholds = {
    "GLUCOSE": {"min": 50, "max": 500, "unit": "mg/dL"},
    "HGB":     {"min": 5,  "max": 20,  "unit": "g/dL"},
    "WBC":     {"min": 1,  "max": 100, "unit": "10^3/uL"},
    "PLT":     {"min": 10, "max": 1500,"unit": "10^3/uL"},
    "CREAT":   {"min": 0.3,"max": 15,  "unit": "mg/dL"},
    "ALT":     {"min": 1,  "max": 2000,"unit": "U/L"},
    "AST":     {"min": 1,  "max": 2000,"unit": "U/L"},
}
with open(workspace / "references/outlier_thresholds.json", "w") as f:
    json.dump(outlier_thresholds, f, indent=2)

# ── Messy raw LB data (the actual task input) ─────────────────────────────────
# Intentionally messy:
#   - Column names DON'T match SDTM (non-standard CRO export names) for some cols
#   - Missing values in numeric columns
#   - Outlier values beyond clinical thresholds
#   - Mixed date formats
#   - LBCAT is present but LBSTRESC is missing -> validation will warn

n = 60
random.seed(42)
np.random.seed(42)

subjects = [f"ONCO-2023-00{i:03d}-001" for i in range(1, n + 1)]
studyids = ["ONCO-2023"] * n
# Mix of test codes
test_codes = np.random.choice(["GLUCOSE", "HGB", "WBC", "CREAT", "ALT", "AST", "PLT"], n)
categories = {
    "GLUCOSE": "CHEMISTRY", "HGB": "HEMATOLOGY", "WBC": "HEMATOLOGY",
    "CREAT": "CHEMISTRY", "ALT": "CHEMISTRY", "AST": "CHEMISTRY", "PLT": "HEMATOLOGY"
}
units_map = {
    "GLUCOSE": "mg/dL", "HGB": "g/dL", "WBC": "10^3/uL",
    "CREAT": "mg/dL", "ALT": "U/L", "AST": "U/L", "PLT": "10^3/uL"
}
# Normal values range
normal_values = {
    "GLUCOSE": (80, 120), "HGB": (12, 17), "WBC": (4, 11),
    "CREAT": (0.6, 1.2), "ALT": (10, 40), "AST": (10, 40), "PLT": (150, 400)
}

lborres_vals = []
for tc in test_codes:
    lo, hi = normal_values[tc]
    lborres_vals.append(round(np.random.uniform(lo, hi), 2))

# Inject outliers at specific indices
outlier_indices = [5, 12, 27, 38, 51]
outlier_values = {
    5:  ("GLUCOSE", 540.0),   # > 500 threshold
    12: ("HGB", 1.2),         # < 5 threshold
    27: ("CREAT", 22.5),      # > 15 threshold
    38: ("ALT", 2500.0),      # > 2000 threshold
    51: ("WBC", 0.3),         # < 1 threshold
}
for idx, (tc, val) in outlier_values.items():
    test_codes[idx] = tc
    lborres_vals[idx] = val

# Inject missing values
missing_indices = [3, 17, 33, 45]
for mi in missing_indices:
    lborres_vals[mi] = np.nan

# Mixed date formats (intentionally messy)
date_formats_pool = [
    lambda d: d.strftime("%Y-%m-%d"),
    lambda d: d.strftime("%d/%m/%Y"),
    lambda d: d.strftime("%m/%d/%Y"),
    lambda d: d.strftime("%d-%b-%Y"),
    lambda d: d.strftime("%Y-%m-%dT%H:%M:%S"),
]
from datetime import date, timedelta
base_date = date(2023, 6, 1)
dates = []
for i in range(n):
    d = base_date + timedelta(days=i % 180)
    fmt = date_formats_pool[i % len(date_formats_pool)]
    dates.append(fmt(d))

# CRITICAL: Use NON-SDTM column names to simulate CRO export
# LBSTRESC is deliberately missing (must be caught by validation)
# LBCAT is present
# Use "LAB_RESULT" instead of "LBORRES" -- wait, let me make it valid SDTM names
# but LBSTRESC is missing and one required field is absent
# Actually let's keep LBORRES as the right name but drop LBSTRESC entirely
# so the cleaner warns but can still proceed

raw_lb = pd.DataFrame({
    "STUDYID":  studyids,
    "USUBJID":  subjects,
    "LBTESTCD": test_codes,
    "LBCAT":    [categories[tc] for tc in test_codes],
    "LBORRES":  lborres_vals,
    "LBORRESU": [units_map[tc] for tc in test_codes],
    # LBSTRESC intentionally MISSING — critical required field absent
    "LBDTC":    dates,
    # Extra non-SDTM columns (noise from CRO export)
    "CRO_SUBJECT_ID": [f"CRO-{i:04d}" for i in range(n)],
    "LAB_VENDOR": ["CentralLab Corp"] * n,
    "BATCH_ID":  [f"BATCH-{i//10 + 1}" for i in range(n)],
})

raw_lb.to_csv(workspace / "raw_data/lb_oncology_raw.csv", index=False)

print("Workspace generation complete.")
print(f"Raw LB file: {workspace}/raw_data/lb_oncology_raw.csv")
print(f"Rows: {len(raw_lb)}, Columns: {list(raw_lb.columns)}")
print(f"Missing LBSTRESC: YES (required field)")
print(f"Outlier rows injected: {outlier_indices}")
print(f"Missing value rows injected: {missing_indices}")