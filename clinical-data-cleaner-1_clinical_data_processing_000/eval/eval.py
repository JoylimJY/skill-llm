#!/usr/bin/env python3
"""
Evaluation script for the clinical-data-cleaner LB domain task.
"""
import json
import sys
import traceback
from pathlib import Path

import pandas as pd
import numpy as np

def run_checks(workspace: str):
    checks = []
    workspace = Path(workspace)

    # ── CHECK 1: Output CSV file exists ────────────────────────────────────
    try:
        csv_files = list(workspace.rglob("lb_clean_onco2026.csv"))
        if not csv_files:
            checks.append({"name": "output_csv_exists", "passed": False,
                           "detail": "lb_clean_onco2026.csv not found anywhere in workspace"})
        else:
            checks.append({"name": "output_csv_exists", "passed": True,
                           "detail": f"Found at {csv_files[0]}"})
    except Exception as e:
        checks.append({"name": "output_csv_exists", "passed": False, "detail": str(e)})

    # ── CHECK 2: Audit report JSON exists ──────────────────────────────────
    try:
        json_files = list(workspace.rglob("lb_clean_onco2026.report.json"))
        if not json_files:
            checks.append({"name": "audit_report_json_exists", "passed": False,
                           "detail": "lb_clean_onco2026.report.json not found anywhere in workspace"})
        else:
            checks.append({"name": "audit_report_json_exists", "passed": True,
                           "detail": f"Found at {json_files[0]}"})
    except Exception as e:
        checks.append({"name": "audit_report_json_exists", "passed": False, "detail": str(e)})

    # ── Early exit if no output files ──────────────────────────────────────
    csv_files = list(workspace.rglob("lb_clean_onco2026.csv"))
    json_files = list(workspace.rglob("lb_clean_onco2026.report.json"))
    if not csv_files or not json_files:
        # Add remaining checks as failed
        for name in ["correct_domain_lb", "outlier_flag_columns_present",
                     "domain_outliers_flagged_correctly", "missing_values_imputed",
                     "dates_standardized_iso8601", "audit_trail_has_entries",
                     "audit_domain_method_recorded", "row_count_preserved"]:
            checks.append({"name": name, "passed": False,
                           "detail": "Cannot evaluate: output file(s) missing"})
        return checks

    csv_path  = csv_files[0]
    json_path = json_files[0]

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        for name in ["correct_domain_lb", "outlier_flag_columns_present",
                     "domain_outliers_flagged_correctly", "missing_values_imputed",
                     "dates_standardized_iso8601", "audit_trail_has_entries",
                     "audit_domain_method_recorded", "row_count_preserved"]:
            checks.append({"name": name, "passed": False,
                           "detail": f"Failed to read CSV: {e}"})
        return checks

    try:
        with open(json_path) as f:
            report = json.load(f)
    except Exception as e:
        report = {}

    # ── CHECK 3: LB domain columns present ─────────────────────────────────
    try:
        lb_required = ['STUDYID','USUBJID','LBTESTCD','LBCAT','LBORRES','LBORRESU','LBSTRESC','LBDTC']
        missing_cols = [c for c in lb_required if c not in df.columns]
        if missing_cols:
            checks.append({"name": "correct_domain_lb", "passed": False,
                           "detail": f"Missing LB domain columns: {missing_cols}"})
        else:
            checks.append({"name": "correct_domain_lb", "passed": True,
                           "detail": "All LB required SDTM fields present"})
    except Exception as e:
        checks.append({"name": "correct_domain_lb", "passed": False, "detail": str(e)})

    # ── CHECK 4: Outlier flag columns present ───────────────────────────────
    try:
        flag_cols = [c for c in df.columns if c.endswith('_OUTLIER_FLAG')]
        if not flag_cols:
            checks.append({"name": "outlier_flag_columns_present", "passed": False,
                           "detail": "No *_OUTLIER_FLAG columns found. Agent may have used wrong outlier_action."})
        else:
            checks.append({"name": "outlier_flag_columns_present", "passed": True,
                           "detail": f"Flag columns found: {flag_cols}"})
    except Exception as e:
        checks.append({"name": "outlier_flag_columns_present", "passed": False, "detail": str(e)})

    # ── CHECK 5: Domain-based outliers correctly flagged ───────────────────
    # The raw data has: GLUCOSE row 5 = 620 (>500), row 11 = 25 (<50),
    # HGB row 3 = 1.8 (<5), row 17 = 24.5 (>20)
    # With --outlier-method domain, LBORRES_OUTLIER_FLAG should be 1 for those rows.
    try:
        lborres_flag = 'LBORRES_OUTLIER_FLAG'
        if lborres_flag not in df.columns:
            checks.append({"name": "domain_outliers_flagged_correctly", "passed": False,
                           "detail": f"{lborres_flag} column not found"})
        else:
            # After median imputation, the indices 3, 5, 11, 17 should be flagged=1
            # (The row order should be preserved)
            flagged_indices = df.index[df[lborres_flag] == 1].tolist()
            expected_flagged = {3, 5, 11, 17}
            flagged_set = set(flagged_indices)
            # We expect all 4 extreme values to be caught
            caught = expected_flagged.intersection(flagged_set)
            if len(caught) >= 3:  # allow 1 miss due to imputation edge cases
                checks.append({"name": "domain_outliers_flagged_correctly", "passed": True,
                               "detail": f"Domain-threshold outliers flagged at rows {sorted(caught)} (expected {sorted(expected_flagged)})"})
            else:
                checks.append({"name": "domain_outliers_flagged_correctly", "passed": False,
                               "detail": f"Only {len(caught)}/4 expected outlier rows flagged. "
                                        f"Got flagged rows: {sorted(flagged_set)}. "
                                        f"Expected (subset): {sorted(expected_flagged)}. "
                                        "Verify --outlier-method domain was used."})
    except Exception as e:
        checks.append({"name": "domain_outliers_flagged_correctly", "passed": False,
                       "detail": f"Error checking outlier flags: {e}\n{traceback.format_exc()}"})

    # ── CHECK 6: Missing values were imputed (no NaN in LBORRES) ───────────
    try:
        n_missing_after = df['LBORRES'].isna().sum() if 'LBORRES' in df.columns else -1
        if n_missing_after == 0:
            checks.append({"name": "missing_values_imputed", "passed": True,
                           "detail": "LBORRES has 0 missing values after imputation"})
        elif n_missing_after == -1:
            checks.append({"name": "missing_values_imputed", "passed": False,
                           "detail": "LBORRES column not found"})
        else:
            checks.append({"name": "missing_values_imputed", "passed": False,
                           "detail": f"LBORRES still has {n_missing_after} missing values. Imputation may not have run."})
    except Exception as e:
        checks.append({"name": "missing_values_imputed", "passed": False, "detail": str(e)})

    # ── CHECK 7: Dates standardized to ISO 8601 ────────────────────────────
    try:
        if 'LBDTC' not in df.columns:
            checks.append({"name": "dates_standardized_iso8601", "passed": False,
                           "detail": "LBDTC column not found"})
        else:
            # ISO 8601 pattern: YYYY-MM-DDTHH:MM:SS
            iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'
            non_iso = df['LBDTC'].dropna().apply(
                lambda x: not bool(__import__('re').match(iso_pattern, str(x)))
            )
            n_non_iso = non_iso.sum()
            n_total = len(df['LBDTC'].dropna())
            frac_iso = (n_total - n_non_iso) / n_total if n_total > 0 else 0
            if frac_iso >= 0.85:
                checks.append({"name": "dates_standardized_iso8601", "passed": True,
                               "detail": f"{n_total - n_non_iso}/{n_total} LBDTC values in ISO 8601 format"})
            else:
                # Show sample non-ISO values
                sample_bad = df['LBDTC'][non_iso].head(3).tolist()
                checks.append({"name": "dates_standardized_iso8601", "passed": False,
                               "detail": f"Only {n_total-n_non_iso}/{n_total} dates in ISO 8601. "
                                        f"Sample non-ISO values: {sample_bad}"})
    except Exception as e:
        checks.append({"name": "dates_standardized_iso8601", "passed": False, "detail": str(e)})

    # ── CHECK 8: Audit trail present in report JSON ────────────────────────
    try:
        if not report:
            checks.append({"name": "audit_trail_has_entries", "passed": False,
                           "detail": "Report JSON is empty or could not be read"})
        else:
            audit = report.get('audit_trail', [])
            if len(audit) >= 3:
                checks.append({"name": "audit_trail_has_entries", "passed": True,
                               "detail": f"Audit trail has {len(audit)} entries"})
            else:
                checks.append({"name": "audit_trail_has_entries", "passed": False,
                               "detail": f"Audit trail has only {len(audit)} entries (expected ≥3)"})
    except Exception as e:
        checks.append({"name": "audit_trail_has_entries", "passed": False, "detail": str(e)})

    # ── CHECK 9: Report records domain=LB and outlier_method=domain ────────
    try:
        if not report:
            checks.append({"name": "audit_domain_method_recorded", "passed": False,
                           "detail": "Report JSON missing"})
        else:
            domain_ok  = report.get('domain', '').upper() == 'LB'
            config     = report.get('configuration', {})
            method_ok  = config.get('outlier_method', '').lower() == 'domain'
            action_ok  = config.get('outlier_action', '').lower() == 'flag'
            strategy_ok = config.get('missing_strategy', '').lower() == 'median'
            all_ok = domain_ok and method_ok and action_ok and strategy_ok
            detail = (f"domain={report.get('domain')}, "
                      f"outlier_method={config.get('outlier_method')}, "
                      f"outlier_action={config.get('outlier_action')}, "
                      f"missing_strategy={config.get('missing_strategy')}")
            checks.append({"name": "audit_domain_method_recorded", "passed": all_ok,
                           "detail": detail})
    except Exception as e:
        checks.append({"name": "audit_domain_method_recorded", "passed": False, "detail": str(e)})

    # ── CHECK 10: Row count preserved (60 rows) ────────────────────────────
    try:
        n_rows = len(df)
        # With flag action rows are preserved; with remove they'd be fewer
        if n_rows == 60:
            checks.append({"name": "row_count_preserved", "passed": True,
                           "detail": f"Output has {n_rows} rows (expected 60)"})
        elif 55 <= n_rows < 60:
            checks.append({"name": "row_count_preserved", "passed": False,
                           "detail": f"Output has {n_rows} rows instead of 60. "
                                    "Was --outlier-action remove used instead of flag?"})
        else:
            checks.append({"name": "row_count_preserved", "passed": False,
                           "detail": f"Unexpected row count: {n_rows} (expected 60)"})
    except Exception as e:
        checks.append({"name": "row_count_preserved", "passed": False, "detail": str(e)})

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = run_checks(workspace)
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    result = {
        "passed": passed_count == total,
        "score":  score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()