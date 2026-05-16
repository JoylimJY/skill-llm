import sys
import json
import csv
import io
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    score = 0.0

    # ── 1. Find the output file ────────────────────────────────────────────
    # The prompt asks to save as clean_patient_intake_2024.csv
    expected_filename = "clean_patient_intake_2024.csv"
    found_files = list(Path(workspace).rglob(expected_filename))

    if not found_files:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": f"File '{expected_filename}' not found anywhere in workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    output_path = found_files[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found at {output_path}"
    })
    score += 0.1

    # ── 2. Load the output CSV ─────────────────────────────────────────────
    try:
        import pandas as pd
        import numpy as np
        df = pd.read_csv(str(output_path), encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Failed to read CSV: {e}"
        })
        return {"passed": False, "score": score, "checks": checks}

    checks.append({
        "name": "output_file_readable",
        "passed": True,
        "detail": f"CSV loaded successfully. Shape: {df.shape}"
    })
    score += 0.05

    # ── 3. Load original file to derive expected values ────────────────────
    original_path = Path(workspace) / "hospital_data/exports/raw/patient_intake_2024.csv"
    try:
        df_orig = pd.read_csv(str(original_path), encoding="utf-8", skipinitialspace=True)
        # Strip whitespace from object columns
        for col in df_orig.columns:
            if df_orig[col].dtype == object:
                df_orig[col] = df_orig[col].str.strip()
    except Exception as e:
        checks.append({
            "name": "original_file_readable",
            "passed": False,
            "detail": f"Could not read original: {e}"
        })
        return {"passed": False, "score": score, "checks": checks}

    # ── 4. Check: duplicates were dropped ─────────────────────────────────
    df_dedup = df_orig.drop_duplicates()
    expected_row_count = len(df_dedup)
    actual_row_count = len(df)

    dup_dropped = (actual_row_count == expected_row_count)
    checks.append({
        "name": "duplicates_dropped",
        "passed": dup_dropped,
        "detail": (
            f"Expected {expected_row_count} rows after dedup, got {actual_row_count}. "
            f"Original had {len(df_orig)} rows."
        )
    })
    if dup_dropped:
        score += 0.25

    # ── 5. Check: column names standardized to snake_case ─────────────────
    def to_snake_expected(name):
        name = name.strip()
        name = re.sub(r'[\s\-]+', '_', name)
        name = re.sub(r'[^\w]', '', name)
        name = re.sub(r'([A-Z])', r'_\1', name).lower()
        name = re.sub(r'_+', '_', name).strip('_')
        return name

    expected_cols = [to_snake_expected(c) for c in df_orig.columns]
    actual_cols = list(df.columns)

    cols_match = (actual_cols == expected_cols)
    checks.append({
        "name": "column_names_standardized",
        "passed": cols_match,
        "detail": f"Expected cols: {expected_cols}. Got: {actual_cols}"
    })
    if cols_match:
        score += 0.25

    # ── 6. Check: missing numeric values filled with MEDIAN (not mean) ─────
    # After dedup, compute median from original (deduped) data for numeric cols
    # and verify no NaN remains in numeric columns of output

    numeric_orig_cols = df_dedup.select_dtypes(include=[np.number]).columns.tolist()

    # Map original col names to expected snake_case
    col_map = {orig: to_snake_expected(orig) for orig in df_dedup.columns}

    # Check that output numeric columns have no NaN
    if cols_match:
        numeric_out_cols = [col_map[c] for c in numeric_orig_cols if col_map[c] in df.columns]
    else:
        # Try to find by position
        numeric_out_cols = [c for c in df.select_dtypes(include=[np.number]).columns]

    no_nan_in_numeric = True
    nan_detail = []
    for col in numeric_out_cols:
        if col in df.columns:
            n_null = df[col].isnull().sum()
            if n_null > 0:
                no_nan_in_numeric = False
                nan_detail.append(f"{col}: {n_null} nulls remain")

    checks.append({
        "name": "missing_numeric_filled",
        "passed": no_nan_in_numeric,
        "detail": (
            "All numeric columns have no missing values." if no_nan_in_numeric
            else f"Missing values remain: {nan_detail}"
        )
    })
    if no_nan_in_numeric:
        score += 0.15

    # ── 7. Check: values filled with MEDIAN (not mean) ────────────────────
    # Compute expected medians from deduped original data
    median_correct = True
    median_details = []

    for orig_col in numeric_orig_cols:
        snake_col = col_map[orig_col]
        if snake_col not in df.columns:
            continue

        series_orig = pd.to_numeric(df_dedup[orig_col], errors='coerce')
        expected_median = series_orig.median()
        expected_mean = series_orig.mean()

        # Find rows where original was NaN → check output has median
        nan_mask = series_orig.isna()
        if nan_mask.sum() == 0:
            continue

        # We need to align by row. After dedup+standardize names but BEFORE fill,
        # what rows had NaN? We'll check output values for those positions.
        # Use the index of df_dedup that had NaN
        nan_indices = df_dedup[nan_mask].index.tolist()

        # The output df should have the same rows (just cleaned).
        # Try to match by other non-null columns (patient_id)
        pid_col_orig = "Patient ID"
        pid_col_out = col_map.get(pid_col_orig, "patient_id")

        if pid_col_out in df.columns and pid_col_orig in df_dedup.columns:
            nan_patient_ids = df_dedup.loc[nan_mask, pid_col_orig].tolist()
            for pid_val in nan_patient_ids:
                out_rows = df[df[pid_col_out] == pid_val]
                if out_rows.empty:
                    continue
                out_val = out_rows[snake_col].values[0]
                # Check it's close to median (not mean)
                if abs(float(out_val) - expected_median) > 0.01:
                    # Check if it's the mean instead
                    if abs(float(out_val) - expected_mean) < 0.01:
                        median_correct = False
                        median_details.append(
                            f"Col '{snake_col}' pid={pid_val}: got {out_val} (mean={expected_mean:.2f}), expected median={expected_median:.2f}"
                        )
                    else:
                        median_details.append(
                            f"Col '{snake_col}' pid={pid_val}: got {out_val}, expected median={expected_median:.2f} (unexpected value)"
                        )

    checks.append({
        "name": "filled_with_median_not_mean",
        "passed": median_correct,
        "detail": (
            "Numeric fills match median strategy." if median_correct
            else "; ".join(median_details) if median_details else "Could not verify median values."
        )
    })
    if median_correct and no_nan_in_numeric:
        score += 0.20

    # ── 8. Non-numeric columns untouched (no spurious fills) ──────────────
    non_numeric_orig = [c for c in df_dedup.columns if c not in numeric_orig_cols]
    non_numeric_ok = True
    nn_detail = []

    for orig_col in non_numeric_orig:
        snake_col = col_map[orig_col]
        if snake_col not in df.columns:
            continue
        orig_nulls = df_dedup[orig_col].isnull().sum()
        out_nulls = df[snake_col].isnull().sum() if snake_col in df.columns else -1
        # Non-numeric NaN should remain NaN (median strategy only fills numeric)
        # Allow that output may have same or fewer nulls (mode wouldn't be wrong per se,
        # but median strategy spec says "only numeric cols")
        # We just ensure no spurious constant fill like "0" or "median" string
        if orig_nulls > 0 and out_nulls == 0:
            # Check if the filled values look like a numeric fill (suspicious)
            filled_vals = df[snake_col].unique().tolist()
            # This is a soft check: warn but don't fail hard
            nn_detail.append(f"Non-numeric col '{snake_col}': orig had {orig_nulls} nulls, output has 0 (may have been filled unexpectedly).")

    non_numeric_ok = len(nn_detail) == 0
    checks.append({
        "name": "non_numeric_columns_handling",
        "passed": True,  # Soft check, informational
        "detail": "; ".join(nn_detail) if nn_detail else "Non-numeric columns handled as expected."
    })
    score += 0.0  # informational only

    # ── Final scoring ──────────────────────────────────────────────────────
    # Cap score at 1.0
    score = min(round(score, 4), 1.0)

    critical_checks = [
        "output_file_exists",
        "duplicates_dropped",
        "column_names_standardized",
        "missing_numeric_filled",
    ]
    passed_critical = all(c["passed"] for c in checks if c["name"] in critical_checks)

    return {
        "passed": passed_critical,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))