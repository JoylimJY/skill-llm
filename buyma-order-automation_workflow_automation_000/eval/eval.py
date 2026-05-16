#!/usr/bin/env python3
"""
Evaluation script for buyma-order-automation ad hoc range task.
Checks:
  1. Output file exists with correct naming pattern tmazonORDERLISTYYMMDD_124100-124115.xlsx
  2. Correct order range: orders 124100–124115 (16 rows)
  3. Memo rules correctly applied (prepend vs. no-rewrite)
  4. enrich_from_history ran (I/J/M fields populated where history exists)
  5. state/last_run.json updated with last_order=124115 and mode=adhoc
  6. Base file selection: incoming/ was used as base (last_order_number=124099 anchor)
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime

try:
    import openpyxl
    import pandas as pd
except ImportError as e:
    print(json.dumps({
        "passed": False, "score": 0.0,
        "checks": [{"name": "imports", "passed": False, "detail": str(e)}]
    }))
    sys.exit(0)

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
checks = []

# ─── Helper ────────────────────────────────────────────────────────────────────
def is_valid_6digit(s):
    return bool(re.fullmatch(r'\d{6}', str(s).strip()))

# ─── Check 1: Output file exists with correct name ─────────────────────────────
output_file = None
try:
    # Pattern: tmazonORDERLISTYYMMDD_124100-124115.xlsx
    pattern = re.compile(r'tmazonORDERLIST\d{6}_124100-124115\.xlsx$')
    candidates = list(workspace.rglob("tmazonORDERLIST*_124100-124115.xlsx"))
    if candidates:
        output_file = candidates[0]
        checks.append({
            "name": "output_file_exists",
            "passed": True,
            "detail": f"Found: {output_file}"
        })
    else:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "No file matching tmazonORDERLIST*_124100-124115.xlsx found anywhere in workspace"
        })
except Exception as ex:
    checks.append({"name": "output_file_exists", "passed": False, "detail": str(ex)})

# ─── Check 2: Correct order range (16 rows, ids 124100–124115) ─────────────────
order_rows = []
if output_file:
    try:
        wb = openpyxl.load_workbook(str(output_file))
        ws = wb.active
        headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
        order_rows = list(ws.iter_rows(min_row=2, values_only=True))
        order_ids = []
        for row in order_rows:
            try:
                order_ids.append(int(str(row[0]).strip()))
            except Exception:
                pass
        expected_ids = list(range(124100, 124116))
        present = sorted(order_ids)
        ok = (present == expected_ids)
        checks.append({
            "name": "correct_order_range",
            "passed": ok,
            "detail": f"Expected 124100-124115 (16 rows), got {present}"
        })
    except Exception as ex:
        checks.append({"name": "correct_order_range", "passed": False, "detail": str(ex)})
else:
    checks.append({"name": "correct_order_range", "passed": False, "detail": "No output file to check"})

# ─── Check 3: Memo rules applied correctly ─────────────────────────────────────
# Original CSV memo states (from gen_inputs_script, seed=42):
#   i % 3 == 0 → str(i)           = 6-digit → NO rewrite → memo stays as str(i)
#   i % 3 == 1 → str(i % 1000)    = short   → PREPEND order_id
#   i % 3 == 2 → "要確認"           = text    → PREPEND order_id
memo_check_passed = True
memo_details = []

if output_file and order_rows:
    try:
        wb2 = openpyxl.load_workbook(str(output_file))
        ws2 = wb2.active
        headers2 = [cell.value for cell in next(ws2.iter_rows(min_row=1, max_row=1))]
        col_idx = {h: i for i, h in enumerate(headers2)}
        k_col = col_idx.get("K_memo")
        a_col = col_idx.get("A_order_id")

        for row in ws2.iter_rows(min_row=2, values_only=True):
            try:
                oid = int(str(row[a_col]).strip())
            except Exception:
                continue
            memo = str(row[k_col]).strip() if row[k_col] is not None else ""

            if oid % 3 == 0:
                # Was already valid 6-digit → should NOT be rewritten (stays as str(oid))
                expected = str(oid)
                if memo != expected:
                    memo_check_passed = False
                    memo_details.append(f"Order {oid}: memo should stay '{expected}', got '{memo}'")
            elif oid % 3 == 1:
                # Short number → prepend: "OIDSTR SHORTNUM"
                short = str(oid % 1000)
                expected_prefix = str(oid).zfill(6)
                if not memo.startswith(expected_prefix):
                    memo_check_passed = False
                    memo_details.append(f"Order {oid}: memo should start with '{expected_prefix}', got '{memo}'")
                # Also check the original content is still present
                if short not in memo:
                    memo_check_passed = False
                    memo_details.append(f"Order {oid}: original short memo '{short}' missing from '{memo}'")
            else:
                # Text → prepend: "OIDSTR 要確認"
                expected_prefix = str(oid).zfill(6)
                if not memo.startswith(expected_prefix):
                    memo_check_passed = False
                    memo_details.append(f"Order {oid}: memo should start with '{expected_prefix}', got '{memo}'")
                if "要確認" not in memo:
                    memo_check_passed = False
                    memo_details.append(f"Order {oid}: original text '要確認' missing from '{memo}'")

        checks.append({
            "name": "memo_rules_applied",
            "passed": memo_check_passed,
            "detail": "; ".join(memo_details) if memo_details else "All memo rules correctly applied"
        })
    except Exception as ex:
        checks.append({"name": "memo_rules_applied", "passed": False, "detail": str(ex)})
else:
    checks.append({"name": "memo_rules_applied", "passed": False, "detail": "No output file / rows to check"})

# ─── Check 4: Enrich from history ran (I_category, J_supplier populated) ───────
# History covers 123990-124010, which is OUTSIDE 124100-124115,
# so enrichment won't match by order_id — but the workbook must have
# I_category and J_supplier columns present (from the build step at minimum).
# We verify the columns exist and at least the G/H/L columns are filled from CSV.
if output_file:
    try:
        wb3 = openpyxl.load_workbook(str(output_file))
        ws3 = wb3.active
        headers3 = [cell.value for cell in next(ws3.iter_rows(min_row=1, max_row=1))]
        required_cols = ["I_category", "J_supplier", "M_note", "G_shipping", "H_tracking"]
        missing = [c for c in required_cols if c not in headers3]
        # Check that G_shipping and H_tracking are populated (came from CSV)
        g_col = headers3.index("G_shipping") if "G_shipping" in headers3 else None
        h_col = headers3.index("H_tracking") if "H_tracking" in headers3 else None
        populated = True
        for row in ws3.iter_rows(min_row=2, values_only=True):
            if g_col is not None and not row[g_col]:
                populated = False
            if h_col is not None and not row[h_col]:
                populated = False
        ok = not missing and populated
        checks.append({
            "name": "enrich_columns_present_and_csv_populated",
            "passed": ok,
            "detail": f"Missing cols: {missing}; G/H populated: {populated}"
        })
    except Exception as ex:
        checks.append({"name": "enrich_columns_present_and_csv_populated", "passed": False, "detail": str(ex)})
else:
    checks.append({"name": "enrich_columns_present_and_csv_populated", "passed": False, "detail": "No output file"})

# ─── Check 5: state/last_run.json updated ──────────────────────────────────────
state_path = workspace / ".openclaw/workspace/buyma_order/state/last_run.json"
try:
    state_data = json.loads(state_path.read_text(encoding="utf-8"))
    last_order_ok = int(state_data.get("last_order", 0)) == 124115
    mode_ok = state_data.get("mode", "").lower() in ("adhoc", "ad_hoc", "ad hoc", "range")
    ok = last_order_ok and mode_ok
    checks.append({
        "name": "state_updated",
        "passed": ok,
        "detail": f"last_order={state_data.get('last_order')}, mode={state_data.get('mode')}"
    })
except Exception as ex:
    checks.append({"name": "state_updated", "passed": False, "detail": str(ex)})

# ─── Check 6: Base file selection used incoming/ (anchor = 124099) ─────────────
# Verify the agent used the incoming file as anchor:
# The incoming file has last order 124099, so the new range starts at 124100.
# If the agent had used current/ (last order 124070) they might have started from 124071.
# We verify the output range starts at 124100 (already tested in check 2), AND
# verify the incoming file was NOT deleted/modified (still present).
try:
    incoming_dir = workspace / ".openclaw/workspace/buyma_order/orders/incoming"
    incoming_files = list(incoming_dir.glob("*.xlsx"))
    base_anchor_ok = any("124099" in f.name or "124085" in f.name for f in incoming_files)
    # Additionally verify range starts exactly at 124100 (not 124071 which would indicate current/ was used)
    if output_file and order_rows:
        wb_chk = openpyxl.load_workbook(str(output_file))
        ws_chk = wb_chk.active
        all_ids = []
        for row in ws_chk.iter_rows(min_row=2, values_only=True):
            try:
                all_ids.append(int(str(row[0]).strip()))
            except Exception:
                pass
        range_start_ok = (min(all_ids) == 124100) if all_ids else False
    else:
        range_start_ok = False
    ok = base_anchor_ok and range_start_ok
    checks.append({
        "name": "base_file_selection_incoming_priority",
        "passed": ok,
        "detail": f"incoming files present: {[f.name for f in incoming_files]}; range_start_ok={range_start_ok}"
    })
except Exception as ex:
    checks.append({"name": "base_file_selection_incoming_priority", "passed": False, "detail": str(ex)})

# ─── Final scoring ─────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
all_passed = (passed_count == total)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2, ensure_ascii=False))