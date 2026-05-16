import os
import json
import random
import pandas as pd
import numpy as np
from pathlib import Path

random.seed(42)
np.random.seed(42)

BASE = Path("/workspace")

# ── Skill directory structure (the actual tool) ──────────────────────────────
skill_dir = BASE / "20260318/scientific-skills/Data Analytics/clinical-data-cleaner"
(skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
(skill_dir / "references").mkdir(parents=True, exist_ok=True)

# Write scripts/main.py — the actual ClinicalDataCleaner implementation
main_py = r'''#!/usr/bin/env python3
"""
Clinical Data Cleaner - SDTM Standardization Tool
Cleans and standardizes clinical trial data for regulatory compliance.
"""
import argparse
import json
import re
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings('ignore')

# SDTM domain required fields
DOMAIN_FIELDS = {
    'DM': ['STUDYID', 'USUBJID', 'SUBJID', 'RFSTDTC', 'RFENDTC', 'SITEID', 'AGE', 'SEX', 'RACE'],
    'LB': ['STUDYID', 'USUBJID', 'LBTESTCD', 'LBCAT', 'LBORRES', 'LBORRESU', 'LBSTRESC', 'LBDTC'],
    'VS': ['STUDYID', 'USUBJID', 'VSTESTCD', 'VSORRES', 'VSORRESU', 'VSSTRESC', 'VSDTC'],
}

# Clinical outlier thresholds
CLINICAL_THRESHOLDS = {
    'GLUCOSE':      {'min': 50,  'max': 500, 'unit': 'mg/dL'},
    'HGB':          {'min': 5,   'max': 20,  'unit': 'g/dL'},
    'SYSBP':        {'min': 70,  'max': 220, 'unit': 'mmHg'},
    'HEMOGLOBIN':   {'min': 5,   'max': 20,  'unit': 'g/dL'},
}


class ClinicalDataCleaner:
    def __init__(self, domain='DM', missing_strategy='median',
                 outlier_method='iqr', outlier_action='flag'):
        self.domain = domain.upper()
        self.missing_strategy = missing_strategy
        self.outlier_method = outlier_method
        self.outlier_action = outlier_action
        self.audit_trail = []
        self._cleaned_data = None

    # ── Validation ─────────────────────────────────────────────────────────
    def validate_domain(self, data):
        required = DOMAIN_FIELDS.get(self.domain, [])
        missing = [f for f in required if f not in data.columns]
        is_valid = len(missing) == 0
        if missing:
            self.audit_trail.append({
                'action': 'validation',
                'status': 'warning',
                'detail': f'Missing required SDTM fields: {missing}'
            })
        else:
            self.audit_trail.append({
                'action': 'validation',
                'status': 'passed',
                'detail': f'All required {self.domain} fields present'
            })
        return is_valid, missing

    # ── Missing values ──────────────────────────────────────────────────────
    def handle_missing_values(self, data):
        df = data.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        imputed_count = 0

        for col in numeric_cols:
            n_missing = df[col].isna().sum()
            if n_missing == 0:
                continue
            if self.missing_strategy == 'mean':
                fill_val = df[col].mean()
            elif self.missing_strategy == 'median':
                fill_val = df[col].median()
            elif self.missing_strategy == 'mode':
                fill_val = df[col].mode().iloc[0] if not df[col].mode().empty else np.nan
            elif self.missing_strategy == 'forward':
                df[col] = df[col].ffill()
                fill_val = None
            elif self.missing_strategy == 'drop':
                df = df.dropna(subset=[col])
                fill_val = None
            else:
                fill_val = df[col].median()

            if fill_val is not None:
                df[col] = df[col].fillna(fill_val)
            imputed_count += n_missing

        self.audit_trail.append({
            'action': 'missing_value_imputation',
            'strategy': self.missing_strategy,
            'records_affected': int(imputed_count)
        })
        return df

    # ── Outlier detection ───────────────────────────────────────────────────
    def detect_outliers(self, data):
        df = data.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_count = 0

        for col in numeric_cols:
            flag_col = f'{col}_OUTLIER_FLAG'
            df[flag_col] = 0

            if self.outlier_method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                mask = (df[col] < lower) | (df[col] > upper)

            elif self.outlier_method == 'zscore':
                z = np.abs(stats.zscore(df[col].dropna()))
                z_full = pd.Series(index=df[col].dropna().index, data=z)
                mask = z_full > 3
                mask = mask.reindex(df.index, fill_value=False)

            elif self.outlier_method == 'domain':
                col_upper = col.upper()
                if col_upper in CLINICAL_THRESHOLDS:
                    thr = CLINICAL_THRESHOLDS[col_upper]
                    mask = (df[col] < thr['min']) | (df[col] > thr['max'])
                else:
                    # Fall back to IQR for unknown parameters
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower = Q1 - 1.5 * IQR
                    upper = Q3 + 1.5 * IQR
                    mask = (df[col] < lower) | (df[col] > upper)
            else:
                mask = pd.Series(False, index=df.index)

            if self.outlier_action == 'flag':
                df.loc[mask, flag_col] = 1
                outlier_count += int(mask.sum())
            elif self.outlier_action == 'remove':
                df = df[~mask]
                outlier_count += int(mask.sum())
                df = df.drop(columns=[flag_col])
            elif self.outlier_action == 'cap':
                if self.outlier_method == 'iqr':
                    df[col] = df[col].clip(lower=lower, upper=upper)
                elif self.outlier_method == 'domain' and col_upper in CLINICAL_THRESHOLDS:
                    thr = CLINICAL_THRESHOLDS[col_upper]
                    df[col] = df[col].clip(lower=thr['min'], upper=thr['max'])
                outlier_count += int(mask.sum())
                df = df.drop(columns=[flag_col])

        self.audit_trail.append({
            'action': 'outlier_detection',
            'method': self.outlier_method,
            'action_taken': self.outlier_action,
            'outliers_found': outlier_count
        })
        return df

    # ── Date standardization ────────────────────────────────────────────────
    def standardize_dates(self, data):
        df = data.copy()
        date_cols = [c for c in df.columns if 'DTC' in c.upper() or 'DATE' in c.upper()]
        standardized = 0

        for col in date_cols:
            converted = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True)
            n_converted = converted.notna().sum()
            df[col] = converted.dt.strftime('%Y-%m-%dT%H:%M:%S').where(converted.notna(), other=df[col])
            standardized += n_converted

        self.audit_trail.append({
            'action': 'date_standardization',
            'format': 'ISO 8601 (YYYY-MM-DDTHH:MM:SS)',
            'fields_standardized': standardized
        })
        return df

    # ── Full pipeline ───────────────────────────────────────────────────────
    def clean(self, data):
        df = data.copy()
        self.validate_domain(df)
        df = self.handle_missing_values(df)
        df = self.detect_outliers(df)
        df = self.standardize_dates(df)
        self._cleaned_data = df
        return df

    # ── Save report ─────────────────────────────────────────────────────────
    def save_report(self, output_path):
        output_path = Path(output_path)
        if self._cleaned_data is None:
            raise RuntimeError("No cleaned data available. Run clean() first.")

        # Save CSV
        self._cleaned_data.to_csv(output_path, index=False)

        # Save audit trail JSON
        report_path = output_path.with_suffix('').with_name(
            output_path.stem + '.report.json'
        )
        report = {
            'tool': 'ClinicalDataCleaner',
            'version': '2.0',
            'domain': self.domain,
            'timestamp': datetime.utcnow().isoformat(),
            'configuration': {
                'missing_strategy': self.missing_strategy,
                'outlier_method': self.outlier_method,
                'outlier_action': self.outlier_action,
            },
            'audit_trail': self.audit_trail,
            'output_file': str(output_path),
        }
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        return str(output_path), str(report_path)


# ── CLI ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='Clinical Data Cleaner - SDTM Standardization Tool'
    )
    parser.add_argument('--input',  required=True, help='Input CSV file path')
    parser.add_argument('--domain', default='DM',
                        choices=['DM', 'LB', 'VS'], help='SDTM domain')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--missing-strategy', default='median',
                        choices=['mean', 'median', 'mode', 'forward', 'drop'],
                        help='Missing value imputation strategy')
    parser.add_argument('--outlier-method', default='iqr',
                        choices=['iqr', 'zscore', 'domain'],
                        help='Outlier detection method')
    parser.add_argument('--outlier-action', default='flag',
                        choices=['flag', 'remove', 'cap'],
                        help='Action to take on detected outliers')
    args = parser.parse_args()

    print(f"Loading data from {args.input}...")
    data = pd.read_csv(args.input)
    print(f"Loaded {len(data)} records, {len(data.columns)} columns")

    cleaner = ClinicalDataCleaner(
        domain=args.domain,
        missing_strategy=args.missing_strategy,
        outlier_method=args.outlier_method,
        outlier_action=args.outlier_action,
    )

    print(f"Cleaning data (domain={args.domain})...")
    cleaned = cleaner.clean(data)
    print(f"Cleaning complete. Output: {len(cleaned)} records")

    csv_out, json_out = cleaner.save_report(args.output)
    print(f"Saved cleaned data  : {csv_out}")
    print(f"Saved audit trail   : {json_out}")
    print("Done.")


if __name__ == '__main__':
    main()
'''

(skill_dir / "scripts" / "main.py").write_text(main_py)

# ── Reference files ────────────────────────────────────────────────────────
sdtm_guide = """# CDISC SDTM Implementation Guide (Summary)

## Domain Overview
- DM: Demographics — one record per subject
- LB: Laboratory Test Results — multiple records per subject
- VS: Vital Signs — multiple records per subject

## Required Variables
See domain_specs.json for machine-readable field lists.

## Date/Time Format
All dates must use ISO 8601: YYYY-MM-DDTHH:MM:SS
"""
(skill_dir / "references" / "sdtm_ig_guide.md").write_text(sdtm_guide)

domain_specs = {
    "DM": {"required": ["STUDYID","USUBJID","SUBJID","RFSTDTC","RFENDTC","SITEID","AGE","SEX","RACE"]},
    "LB": {"required": ["STUDYID","USUBJID","LBTESTCD","LBCAT","LBORRES","LBORRESU","LBSTRESC","LBDTC"]},
    "VS": {"required": ["STUDYID","USUBJID","VSTESTCD","VSORRES","VSORRESU","VSSTRESC","VSDTC"]},
}
(skill_dir / "references" / "domain_specs.json").write_text(json.dumps(domain_specs, indent=2))

outlier_thresholds = {
    "GLUCOSE":    {"min": 50,  "max": 500, "unit": "mg/dL"},
    "HGB":        {"min": 5,   "max": 20,  "unit": "g/dL"},
    "SYSBP":      {"min": 70,  "max": 220, "unit": "mmHg"},
    "HEMOGLOBIN": {"min": 5,   "max": 20,  "unit": "g/dL"},
}
(skill_dir / "references" / "outlier_thresholds.json").write_text(json.dumps(outlier_thresholds, indent=2))

# Write references/common-patterns.md
common_patterns_md = """## Common Patterns

### Pattern 1: Regulatory Submission Preparation
...see skill documentation for full content...
"""
(skill_dir / "references" / "common-patterns.md").write_text(common_patterns_md)

# Write references/troubleshooting.md
troubleshooting_md = """## Troubleshooting

**Problem: Validation fails with missing required fields**
- Check data export settings
- Map field names to SDTM standards

**Problem: Too many outliers detected**
- Use domain-specific thresholds for clinical data
"""
(skill_dir / "references" / "troubleshooting.md").write_text(troubleshooting_md)

# Write requirements.txt
(skill_dir / "requirements.txt").write_text("numpy\npandas\nscipy\n")

# ── Distractor files ───────────────────────────────────────────────────────
distractor_root = BASE / "project_data" / "trial_ONCO2026"

(distractor_root / "raw" / "legacy").mkdir(parents=True, exist_ok=True)
(distractor_root / "raw" / "external_lab").mkdir(parents=True, exist_ok=True)
(distractor_root / "processed" / "interim_q3").mkdir(parents=True, exist_ok=True)
(distractor_root / "docs" / "protocol").mkdir(parents=True, exist_ok=True)
(distractor_root / "docs" / "sap").mkdir(parents=True, exist_ok=True)
(distractor_root / "validation" / "pinnacle21").mkdir(parents=True, exist_ok=True)
(distractor_root / "archive" / "cycle1").mkdir(parents=True, exist_ok=True)

# Distractor: old DM file (wrong domain, red herring)
dm_distractor = pd.DataFrame({
    'STUDYID': ['ONCO2026']*5,
    'USUBJID': [f'ONCO2026-001-{i:03d}' for i in range(1,6)],
    'SUBJID':  [f'001-{i:03d}' for i in range(1,6)],
    'RFSTDTC': ['2025-01-10']*5,
    'RFENDTC': ['2025-06-30']*5,
    'SITEID':  ['001']*5,
    'AGE':     [45, 52, 61, 38, 70],
    'SEX':     ['M','F','M','F','M'],
    'RACE':    ['WHITE']*5,
})
dm_distractor.to_csv(distractor_root / "processed" / "interim_q3" / "dm_interim.csv", index=False)

# Distractor: a VS file (vital signs, not what we need)
vs_distractor = pd.DataFrame({
    'STUDYID':  ['ONCO2026']*6,
    'USUBJID':  [f'ONCO2026-001-{i:03d}' for i in range(1,7)],
    'VSTESTCD': ['SYSBP']*6,
    'VSORRES':  [120, 118, 135, 128, 115, 122],
    'VSORRESU': ['mmHg']*6,
    'VSSTRESC': ['120','118','135','128','115','122'],
    'VSDTC':    ['2025-03-15']*6,
})
vs_distractor.to_csv(distractor_root / "raw" / "legacy" / "vs_legacy.csv", index=False)

# Distractor: config JSON (irrelevant)
config_json = {"study": "ONCO2026", "phase": "III", "sponsor": "PharmaX", "data_lock": "2025-09-01"}
(distractor_root / "docs" / "protocol" / "study_config.json").write_text(json.dumps(config_json, indent=2))

# Distractor: SAP document
(distractor_root / "docs" / "sap" / "statistical_analysis_plan_v2.md").write_text(
    "# Statistical Analysis Plan\n\nPrimary endpoint: Overall Survival at 24 months.\n"
    "Secondary: PFS, ORR, DOR.\n\nAnalysis population: ITT, PP, Safety.\n"
)

# Distractor: pinnacle21 log
(distractor_root / "validation" / "pinnacle21" / "validation_log_draft.txt").write_text(
    "Pinnacle 21 Validation Log\nDate: 2025-08-15\nDomain: LB\nErrors: 3\nWarnings: 7\n"
    "Error 1: LBCAT missing for 12 records\nError 2: LBDTC non-standard format\n"
)

# Distractor: archive readme
(distractor_root / "archive" / "cycle1" / "README_cycle1.txt").write_text(
    "Cycle 1 data archived after database lock on 2025-05-01.\nDo not modify.\n"
)

# Distractor: external lab mapping
mapping = {"HGB": "Hemoglobin", "GLUC": "Glucose", "PLT": "Platelets", "WBC": "White Blood Cells"}
(distractor_root / "raw" / "external_lab" / "lab_code_mapping.json").write_text(
    json.dumps(mapping, indent=2)
)

# Distractor: notes file
(distractor_root / "docs" / "data_manager_notes.txt").write_text(
    "NOTES - Data Manager\n"
    "2025-08-20: Received LB data from central lab. Multiple date formats noted (MM/DD/YYYY and YYYY-MM-DD mixed).\n"
    "Several extreme glucose values need review (>600 mg/dL or <30 mg/dL).\n"
    "HGB values: 2 records below 4 g/dL — possible transcription errors.\n"
    "LBCAT field empty in 15 records from Site 003.\n"
    "Missing LBORRES for 8 records (equipment failure noted in CRF comments).\n"
)

# ── THE ACTUAL TASK INPUT: messy raw LB data ──────────────────────────────
# This is the file the agent must clean.
n = 60
np.random.seed(42)

study_ids  = ['ONCO2026'] * n
usubjids   = [f'ONCO2026-{str(random.randint(1,3)).zfill(3)}-{str(i+1).zfill(3)}' for i in range(n)]
lbtestcds  = np.random.choice(['GLUCOSE', 'HGB', 'GLUC', 'Glucose', 'hgb'], n)  # messy case/names

# LBCAT: intentionally missing for ~15 records
lbcat_vals = []
for i in range(n):
    if i % 4 == 0:
        lbcat_vals.append(np.nan)
    elif lbtestcds[i].upper() in ['GLUCOSE', 'GLUC']:
        lbcat_vals.append('CHEMISTRY')
    else:
        lbcat_vals.append('HEMATOLOGY')

# LBORRES: numeric results with some extreme outliers and some missing
lborres_vals = []
for i in range(n):
    test = lbtestcds[i].upper()
    if i % 8 == 0:
        lborres_vals.append(np.nan)  # missing
    elif test in ['GLUCOSE', 'GLUC']:
        if i == 5:
            lborres_vals.append(620.0)   # extreme outlier (above 500)
        elif i == 11:
            lborres_vals.append(25.0)    # extreme outlier (below 50)
        else:
            lborres_vals.append(round(random.uniform(80, 200), 1))
    else:  # HGB
        if i == 3:
            lborres_vals.append(1.8)     # extreme outlier (below 5)
        elif i == 17:
            lborres_vals.append(24.5)    # extreme outlier (above 20)
        else:
            lborres_vals.append(round(random.uniform(10, 16), 1))

lborresu_vals = ['mg/dL' if t.upper() in ['GLUCOSE','GLUC'] else 'g/dL' for t in lbtestcds]

# LBSTRESC: string result copy (matches LBORRES as string)
lbstresc_vals = [str(v) if not (isinstance(v, float) and np.isnan(v)) else '' for v in lborres_vals]

# LBDTC: mixed date formats (the problematic part)
date_formats = []
base_dates = pd.date_range('2025-01-15', periods=n, freq='3D')
for i, d in enumerate(base_dates):
    if i % 5 == 0:
        date_formats.append(d.strftime('%m/%d/%Y'))         # US format
    elif i % 5 == 1:
        date_formats.append(d.strftime('%d-%b-%Y'))         # 15-Jan-2025
    elif i % 5 == 2:
        date_formats.append(d.strftime('%Y/%m/%d'))         # 2025/01/15
    elif i % 5 == 3:
        date_formats.append(d.strftime('%Y-%m-%d %H:%M'))   # with time, no seconds
    else:
        date_formats.append(d.strftime('%Y-%m-%dT%H:%M:%S')) # already ISO (keep)

raw_lb = pd.DataFrame({
    'STUDYID':  study_ids,
    'USUBJID':  usubjids,
    'LBTESTCD': lbtestcds,
    'LBCAT':    lbcat_vals,
    'LBORRES':  lborres_vals,
    'LBORRESU': lborresu_vals,
    'LBSTRESC': lbstresc_vals,
    'LBDTC':    date_formats,
})

raw_lb_path = distractor_root / "raw" / "lb_raw_onco2026.csv"
raw_lb.to_csv(raw_lb_path, index=False)

print(f"Workspace generated successfully.")
print(f"Raw LB data: {raw_lb_path} ({n} records)")
print(f"Skill dir:   {skill_dir}")