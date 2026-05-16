import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── 1. Find output CSV ────────────────────────────────────────────────────
    csv_files = list(workspace.rglob("lb_clean.csv"))
    if not csv_files:
        add_check("output_csv_exists", False, "lb_clean.csv not found anywhere in workspace")
    else:
        add_check("output_csv_exists", True, f"Found at {csv_files[0]}")

    # ── 2. Find audit report JSON ─────────────────────────────────────────────
    report_files = list(workspace.rglob("lb_clean.report.json"))
    if not report_files:
        add_check("audit_report_exists", False, "lb_clean.report.json not found anywhere in workspace")
    else:
        add_check("audit_report_exists", True, f"Found at {report_files[0]}")

    # If either file is missing we can't do deeper checks; record and bail
    if not csv_files or not report_files:
        total = sum(c["passed"] for c in checks)
        return {
            "passed": False,
            "score": round(total / 8, 3),
            "checks": checks
        }

    csv_path    = csv_files[0]
    report_path = report_files[0]

    # ── 3. Parse CSV ──────────────────────────────────────────────────────────
    try:
        import pandas as pd
        import numpy as np
        df = pd.read_csv(csv_path)
        add_check("output_csv_parseable", True, f"CSV loaded: {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        add_check("output_csv_parseable", False, f"Failed to parse CSV: {e}")
        df = None

    # ── 4. Parse report JSON ──────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
        add_check("audit_report_parseable", True, "Report JSON loaded successfully")
    except Exception as e:
        add_check("audit_report_parseable", False, f"Failed to parse JSON: {e}")
        report = None

    # ── 5. Check domain in report is LB ──────────────────────────────────────
    if report:
        domain_ok = report.get("domain", "").upper() == "LB"
        add_check(
            "report_domain_is_LB",
            domain_ok,
            f"domain in report: '{report.get('domain')}'"
        )
    else:
        add_check("report_domain_is_LB", False, "Report not available")

    # ── 6. Check outlier_method='domain' was used ─────────────────────────────
    # This is THE proprietary trap: agent must NOT use iqr/zscore for LB domain
    if report:
        method_ok = report.get("outlier_method", "").lower() == "domain"
        add_check(
            "outlier_method_is_domain",
            method_ok,
            f"outlier_method in report: '{report.get('outlier_method')}' (must be 'domain')"
        )
    else:
        add_check("outlier_method_is_domain", False, "Report not available")

    # ── 7. Check outlier_action='flag' was used ───────────────────────────────
    if report:
        action_ok = report.get("outlier_action", "").lower() == "flag"
        add_check(
            "outlier_action_is_flag",
            action_ok,
            f"outlier_action in report: '{report.get('outlier_action')}' (must be 'flag')"
        )
    else:
        add_check("outlier_action_is_flag", False, "Report not available")

    # ── 8. Check missing_strategy='median' was used ───────────────────────────
    if report:
        strat_ok = report.get("missing_strategy", "").lower() == "median"
        add_check(
            "missing_strategy_is_median",
            strat_ok,
            f"missing_strategy in report: '{report.get('missing_strategy')}' (must be 'median')"
        )
    else:
        add_check("missing_strategy_is_median", False, "Report not available")

    # ── 9. Validation warning for missing LBSTRESC is logged ─────────────────
    if report:
        audit_messages = " ".join(
            e.get("message", "") for e in report.get("audit_trail", [])
        ).lower()
        lbstresc_warned = "lbstresc" in audit_messages
        add_check(
            "validation_warning_lbstresc_logged",
            lbstresc_warned,
            "Audit trail must contain a warning about missing required field LBSTRESC"
        )
    else:
        add_check("validation_warning_lbstresc_logged", False, "Report not available")

    # ── 10. OUTLIER_FL column exists and clinical outliers are flagged ─────────
    if df is not None:
        if "OUTLIER_FL" in df.columns:
            flagged_rows = (df["OUTLIER_FL"] == "Y").sum()
            # We injected 5 outliers; domain method should catch at least 3
            # (some tests may not be in CLINICAL_THRESHOLDS)
            enough_flagged = flagged_rows >= 3
            add_check(
                "outliers_flagged_with_OUTLIER_FL",
                enough_flagged,
                f"OUTLIER_FL='Y' count: {flagged_rows} (need >= 3 for injected clinical outliers)"
            )
        else:
            add_check(
                "outliers_flagged_with_OUTLIER_FL",
                False,
                "OUTLIER_FL column not found in output CSV (required by domain outlier method)"
            )
    else:
        add_check("outliers_flagged_with_OUTLIER_FL", False, "CSV not available")

    # ── 11. Missing values were imputed (no NaN in LBORRES) ───────────────────
    if df is not None:
        if "LBORRES" in df.columns:
            remaining_missing = df["LBORRES"].isna().sum()
            imputed_ok = remaining_missing == 0
            add_check(
                "missing_values_imputed",
                imputed_ok,
                f"Remaining NaN in LBORRES: {remaining_missing} (should be 0 after median imputation)"
            )
        else:
            add_check("missing_values_imputed", False, "LBORRES column not found in output CSV")
    else:
        add_check("missing_values_imputed", False, "CSV not available")

    # ── 12. Dates are standardized to ISO 8601 ────────────────────────────────
    if df is not None and "LBDTC" in df.columns:
        iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
        non_null_dates = df["LBDTC"].dropna()
        if len(non_null_dates) == 0:
            add_check("dates_standardized_iso8601", False, "No dates found in LBDTC column")
        else:
            pct_iso = sum(bool(iso_pattern.match(str(v))) for v in non_null_dates) / len(non_null_dates)
            dates_ok = pct_iso >= 0.85
            add_check(
                "dates_standardized_iso8601",
                dates_ok,
                f"{pct_iso*100:.1f}% of LBDTC values match ISO 8601 format YYYY-MM-DDTHH:MM:SS (need >= 85%)"
            )
    else:
        add_check(
            "dates_standardized_iso8601",
            False,
            "LBDTC column not found in output CSV or CSV unavailable"
        )

    # ── 13. Audit trail has substantial entries (not trivial) ─────────────────
    if report:
        n_entries = len(report.get("audit_trail", []))
        rich_audit = n_entries >= 10
        add_check(
            "audit_trail_rich",
            rich_audit,
            f"Audit trail entries: {n_entries} (need >= 10 for full pipeline coverage)"
        )
    else:
        add_check("audit_trail_rich", False, "Report not available")

    # ── Score ─────────────────────────────────────────────────────────────────
    total_checks = len(checks)
    passed_checks = sum(c["passed"] for c in checks)
    score = round(passed_checks / total_checks, 3)
    overall_passed = score >= 0.85  # Need to pass at least 85% of checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [], "error": "No workspace path provided"}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))