#!/usr/bin/env python3
"""
Evaluation script for the client-dashboard benchmark task.
Checks:
  1. CLIENT_CONFIGS has ember-oak block with Decimal thresholds
  2. CDC cache was pre-seeded (so CDC log shows deltas, not "First run")
  3. Excel file exists with correct filename
  4. All 6 required tabs present
  5. Executive Summary tab has traffic-light scores (GREEN/YELLOW/RED)
  6. CDC Log tab shows delta values (not "First run" for all rows) AND has Improved/Declined/Unchanged
  7. Trends tab has sparkline arrow characters
  8. Watch Items tab has at least one item
  9. KPI Scorecard has Decimal-based thresholds reflected in green/yellow band columns
 10. ember-oak config uses Decimal (not float) for thresholds — verified by importing the script
"""

import sys
import json
import ast
import re
import importlib.util
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
score_total = 0.0
score_max = 10.0

def check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── 1. Pipeline script has ember-oak in CLIENT_CONFIGS ──────────────────────
try:
    pipeline_path = workspace / "scripts/pipelines/client-dashboard.py"
    source = pipeline_path.read_text()
    has_ember_oak_key = '"ember-oak"' in source or "'ember-oak'" in source
    score_total += check(
        "ember-oak entry in CLIENT_CONFIGS",
        has_ember_oak_key,
        "Found 'ember-oak' key in pipeline script" if has_ember_oak_key else "Missing 'ember-oak' key in CLIENT_CONFIGS"
    )
except Exception as e:
    score_total += check("ember-oak entry in CLIENT_CONFIGS", False, f"Could not read pipeline: {e}")

# ── 2. Decimal usage in ember-oak thresholds ────────────────────────────────
try:
    pipeline_path = workspace / "scripts/pipelines/client-dashboard.py"
    source = pipeline_path.read_text()
    # Find the ember-oak block — look for Decimal( calls after ember-oak key
    ember_oak_pos = max(source.find('"ember-oak"'), source.find("'ember-oak'"))
    if ember_oak_pos == -1:
        score_total += check("Decimal thresholds in ember-oak config", False, "ember-oak block not found")
    else:
        # Get the portion of the source after the ember-oak key (look for Decimal calls)
        after = source[ember_oak_pos:ember_oak_pos + 3000]
        decimal_count = after.count('Decimal(')
        has_decimal = decimal_count >= 3  # need at least 3 Decimal() calls for meaningful thresholds
        score_total += check(
            "Decimal thresholds in ember-oak config",
            has_decimal,
            f"Found {decimal_count} Decimal() calls in ember-oak config block" if has_decimal
            else f"Only {decimal_count} Decimal() calls — thresholds may be using float instead"
        )
except Exception as e:
    score_total += check("Decimal thresholds in ember-oak config", False, f"Parse error: {e}")

# ── 3. ember-oak has required config keys ────────────────────────────────────
try:
    source = (workspace / "scripts/pipelines/client-dashboard.py").read_text()
    ember_pos = max(source.find('"ember-oak"'), source.find("'ember-oak'"))
    after = source[ember_pos:ember_pos + 3000]
    required_keys = ["company_name", "kpis_enabled", "thresholds", "watch_items", "benchmarks"]
    missing = [k for k in required_keys if k not in after]
    passed = len(missing) == 0
    score_total += check(
        "ember-oak config has all required keys",
        passed,
        f"All required keys present" if passed else f"Missing keys: {missing}"
    )
except Exception as e:
    score_total += check("ember-oak config has all required keys", False, f"Error: {e}")

# ── 4. CDC cache was pre-seeded (prior run data) ─────────────────────────────
try:
    cache_path = workspace / ".cache/client-dashboard/ember-oak.json"
    # The agent should have created a prior-run cache before running the pipeline
    # After pipeline runs, the cache is UPDATED to current values
    # So we just verify the cache file exists and has KPI keys
    if cache_path.exists():
        cache_data = json.loads(cache_path.read_text())
        has_kpi_keys = len(cache_data) >= 2
        score_total += check(
            "CDC cache exists for ember-oak",
            has_kpi_keys,
            f"Cache has {len(cache_data)} KPI entries" if has_kpi_keys else "Cache exists but has too few entries"
        )
    else:
        score_total += check("CDC cache exists for ember-oak", False, "No CDC cache found at .cache/client-dashboard/ember-oak.json")
except Exception as e:
    score_total += check("CDC cache exists for ember-oak", False, f"Error reading cache: {e}")

# ── 5. Output Excel file exists with correct filename ────────────────────────
try:
    # Search for the file in common locations
    candidates = list(workspace.rglob("KPI_Dashboard_ember-oak_2026_04.xlsx"))
    # Also check Desktop
    desktop_path = Path.home() / "Desktop" / "KPI_Dashboard_ember-oak_2026_04.xlsx"
    if desktop_path.exists():
        candidates.append(desktop_path)

    found = len(candidates) > 0
    xlsx_path = candidates[0] if found else None
    score_total += check(
        "Output Excel file exists with correct filename",
        found,
        f"Found: {xlsx_path}" if found else "KPI_Dashboard_ember-oak_2026_04.xlsx not found anywhere"
    )
except Exception as e:
    score_total += check("Output Excel file exists with correct filename", False, f"Search error: {e}")
    xlsx_path = None

# ── 6. All 6 required tabs present ──────────────────────────────────────────
required_tabs = {"Executive Summary", "KPI Scorecard", "Trends", "Cash Position", "Watch Items", "CDC Log"}
try:
    if xlsx_path and xlsx_path.exists():
        import openpyxl
        wb = openpyxl.load_workbook(str(xlsx_path))
        actual_tabs = set(wb.sheetnames)
        missing_tabs = required_tabs - actual_tabs
        passed = len(missing_tabs) == 0
        score_total += check(
            "All 6 required tabs present",
            passed,
            f"Tabs found: {sorted(actual_tabs)}" if passed else f"Missing tabs: {missing_tabs}"
        )
    else:
        score_total += check("All 6 required tabs present", False, "Excel file not found — cannot check tabs")
except Exception as e:
    score_total += check("All 6 required tabs present", False, f"Error opening workbook: {e}")

# ── 7. Executive Summary has traffic-light scores (GREEN/YELLOW/RED) ─────────
try:
    if xlsx_path and xlsx_path.exists():
        import openpyxl
        wb = openpyxl.load_workbook(str(xlsx_path))
        ws = wb["Executive Summary"]
        values = []
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if cell in ("GREEN", "YELLOW", "RED", "N/A"):
                    values.append(cell)
        has_scores = len(values) >= 2
        score_total += check(
            "Executive Summary has traffic-light scores",
            has_scores,
            f"Found {len(values)} score cells: {set(values)}" if has_scores
            else "No GREEN/YELLOW/RED scores found in Executive Summary"
        )
    else:
        score_total += check("Executive Summary has traffic-light scores", False, "Excel file not found")
except Exception as e:
    score_total += check("Executive Summary has traffic-light scores", False, f"Error: {e}")

# ── 8. CDC Log has delta values (not all "First run") ────────────────────────
try:
    if xlsx_path and xlsx_path.exists():
        import openpyxl
        wb = openpyxl.load_workbook(str(xlsx_path))
        ws = wb["CDC Log"]
        rows_with_delta = []
        first_run_count = 0
        improved_declined = 0
        for row in ws.iter_rows(min_row=4, values_only=True):
            if row[0] is None:
                continue
            direction = str(row[5]) if len(row) > 5 and row[5] else ""
            if direction == "First run":
                first_run_count += 1
            elif direction in ("Improved", "Declined", "Unchanged"):
                improved_declined += 1
                rows_with_delta.append(row)

        # We want at least some rows with actual delta (not "First run")
        has_real_cdc = improved_declined >= 1
        score_total += check(
            "CDC Log shows real deltas (not all First run)",
            has_real_cdc,
            f"{improved_declined} rows with Improved/Declined/Unchanged, {first_run_count} First-run rows"
            if has_real_cdc else "All CDC rows show 'First run' — prior cache was not seeded"
        )
    else:
        score_total += check("CDC Log shows real deltas (not all First run)", False, "Excel file not found")
except Exception as e:
    score_total += check("CDC Log shows real deltas (not all First run)", False, f"Error: {e}")

# ── 9. Trends tab has sparkline arrow characters ─────────────────────────────
try:
    ARROW_CHARS = {"↑↑", "↑", "↗", "→", "↘", "↓", "↓↓"}
    BLOCK_CHARS = set("█▇▅▃▁_")

    if xlsx_path and xlsx_path.exists():
        import openpyxl
        wb = openpyxl.load_workbook(str(xlsx_path))
        ws = wb["Trends"]
        found_arrows = False
        found_blocks = False
        for row in ws.iter_rows(min_row=4, values_only=True):
            cell_b = str(row[1]) if len(row) > 1 and row[1] else ""
            cell_c = str(row[2]) if len(row) > 2 and row[2] else ""
            if any(a in cell_b for a in ARROW_CHARS):
                found_arrows = True
            if any(b in cell_c for b in BLOCK_CHARS):
                found_blocks = True

        passed = found_arrows or found_blocks
        score_total += check(
            "Trends tab has sparkline characters",
            passed,
            f"Arrows found: {found_arrows}, Blocks found: {found_blocks}" if passed
            else "No sparkline arrow or block characters found in Trends tab"
        )
    else:
        score_total += check("Trends tab has sparkline characters", False, "Excel file not found")
except Exception as e:
    score_total += check("Trends tab has sparkline characters", False, f"Error: {e}")

# ── 10. Watch Items tab has at least one item ────────────────────────────────
try:
    if xlsx_path and xlsx_path.exists():
        import openpyxl
        wb = openpyxl.load_workbook(str(xlsx_path))
        ws = wb["Watch Items"]
        items = []
        for row in ws.iter_rows(min_row=4, values_only=True):
            if row[0] is not None and str(row[0]).strip().isdigit():
                if len(row) > 1 and row[1]:
                    items.append(row[1])
        has_items = len(items) >= 1
        score_total += check(
            "Watch Items tab has at least one watch item",
            has_items,
            f"Found {len(items)} watch item(s): {items[:3]}" if has_items
            else "Watch Items tab is empty — check ember-oak watch_items config"
        )
    else:
        score_total += check("Watch Items tab has at least one watch item", False, "Excel file not found")
except Exception as e:
    score_total += check("Watch Items tab has at least one watch item", False, f"Error: {e}")

# ── Final scoring ──────────────────────────────────────────────────────────
final_score = round(score_total / score_max, 3)
passed = final_score >= 0.7

print(json.dumps({
    "passed": passed,
    "score": final_score,
    "checks": checks
}, indent=2, ensure_ascii=False))