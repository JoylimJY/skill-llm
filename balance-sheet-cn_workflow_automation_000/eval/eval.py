#!/usr/bin/env python3
"""
Evaluation script for the balance sheet generation task.
Usage: python3 eval_script.py <workspace_dir>
"""
import sys
import json
from pathlib import Path

def close_enough(a, b, tol=0.02):
    """Check if two numeric values are within tolerance."""
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    workspace = Path(sys.argv[1])
    checks = []

    # ── Locate output file ────────────────────────────────────────────────────
    output_candidates = list(workspace.rglob("资产负债表.xlsx"))
    if not output_candidates:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "Could not find 资产负债表.xlsx anywhere in the workspace"
        })
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    output_file = output_candidates[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found output file at {output_file}"
    })

    # ── Load the output workbook ──────────────────────────────────────────────
    try:
        import openpyxl
        wb = openpyxl.load_workbook(str(output_file), data_only=True)
        wb_formulas = openpyxl.load_workbook(str(output_file), data_only=False)
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Failed to open output file: {e}"
        })
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    checks.append({
        "name": "output_file_readable",
        "passed": True,
        "detail": "Output file opened successfully"
    })

    # ── Check sheet exists ────────────────────────────────────────────────────
    if "资产负债表" not in wb.sheetnames:
        checks.append({
            "name": "sheet_exists",
            "passed": False,
            "detail": f"Sheet '资产负债表' not found. Available: {wb.sheetnames}"
        })
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    ws = wb["资产负债表"]
    ws_f = wb_formulas["资产负债表"]

    checks.append({
        "name": "sheet_exists",
        "passed": True,
        "detail": "Sheet '资产负债表' exists"
    })

    # ── CHECK: Rule 2 - D column values copied to B column ───────────────────
    # B7 should equal the OLD D7 value (228,843.03) from the source template
    # because rule 2 copies current D values to B BEFORE rule 4 overwrites D7
    # Original D7 in template = 228843.03
    # After rule2: B7 = 228843.03
    # After rule4: D7 = 228843.03 (same in this case - coincidence)
    # But B8 should be old D8 = 78128.70
    # Original D8 in template = 78128.70, after rule5 D8 = 78128.70 (same)
    # Let's check B4 which has formula =B4+C4 in template... actually D4=B4+C4
    # Original D4 = B4+C4 = 850000+0=850000 (C4 formula-based)
    # Actually the real discriminating test: B7 must be 228843.03 (old D7)
    b7_val = ws.cell(row=7, column=2).value
    rule2_b7_ok = close_enough(b7_val, 228843.03)
    checks.append({
        "name": "rule2_b7_last_month_balance",
        "passed": rule2_b7_ok,
        "detail": f"Rule2: B7(上月余额招商银行) expected ~228843.03, got {b7_val}"
    })

    b8_val = ws.cell(row=8, column=2).value
    rule2_b8_ok = close_enough(b8_val, 78128.70)
    checks.append({
        "name": "rule2_b8_last_month_balance",
        "passed": rule2_b8_ok,
        "detail": f"Rule2: B8(上月余额交通银行) expected ~78128.70, got {b8_val}"
    })

    # B14 should be old D14 value. Original D14 formula = B14+C14 = 557069.52 + 29583.54 = 586653.06
    # But in data_only mode the formula might not be evaluated - check if B14 was updated
    # The original template B14 = 557069.52. After rule2, B14 = old D14 computed value.
    # Since openpyxl doesn't compute formulas, old D14 stored = 586653.06? No - it depends on
    # whether the source was saved with cached values. Our gen script saves with openpyxl
    # which does NOT cache formula results. So data_only read of D14 = None (formula, no cache).
    # Rule 2 says copy the "computed value" (公式计算后的值). If source has no cached value,
    # a smart agent would note this and either skip or use the formula string.
    # The SKILL.md says "数值（公式计算后的值）" - for cells with no cached value, B stays unchanged.
    # This is an edge case - we check for B14 being either 557069.52 (unchanged) or the correct computed
    # value. Let's be lenient here.

    # ── CHECK: Rule 3 - C5 = 0 ───────────────────────────────────────────────
    c5_val = ws.cell(row=5, column=3).value
    rule3_ok = (c5_val == 0 or c5_val is None or close_enough(c5_val, 0))
    checks.append({
        "name": "rule3_c5_fixed_assets_zero",
        "passed": rule3_ok,
        "detail": f"Rule3: C5(固定资产合计本月发生额) expected 0, got {c5_val}"
    })

    # ── CHECK: Rule 4 - D7 = 招商银行余额合计 = 27780.68 + 201062.35 = 228843.03 ──
    d7_val = ws.cell(row=7, column=4).value
    rule4_ok = close_enough(d7_val, 228843.03)
    checks.append({
        "name": "rule4_d7_zhaoShang_bank",
        "passed": rule4_ok,
        "detail": f"Rule4: D7(招商银行累计) expected ~228843.03 (sum of 2 rows), got {d7_val}"
    })

    # ── CHECK: Rule 5 - D8 = 交通银行余额合计 = 78128.70 ─────────────────────
    d8_val = ws.cell(row=8, column=4).value
    rule5_ok = close_enough(d8_val, 78128.70)
    checks.append({
        "name": "rule5_d8_jiaotong_bank",
        "passed": rule5_ok,
        "detail": f"Rule5: D8(交通银行累计) expected ~78128.70, got {d8_val}"
    })

    # ── CHECK: Rule 6 - C9 = 应收发生金额合计 = 150000+50000 = 200000 ─────────
    c9_val = ws.cell(row=9, column=3).value
    rule6_ok = close_enough(c9_val, 200000.00)
    checks.append({
        "name": "rule6_c9_receivables",
        "passed": rule6_ok,
        "detail": f"Rule6: C9(应收款合计本月发生额) expected ~200000, got {c9_val}"
    })

    # ── CHECK: Rule 7 - C11 = 预收发生金额合计 = 200000+1736 = 201736 ─────────
    c11_val = ws.cell(row=11, column=3).value
    rule7_ok = close_enough(c11_val, 201736.00)
    checks.append({
        "name": "rule7_c11_advance_receipts",
        "passed": rule7_ok,
        "detail": f"Rule7: C11(预收款本月发生额) expected ~201736, got {c11_val}"
    })

    # ── CHECK: Rule 8 - C12 = 应付发生金额合计 = -50000 ──────────────────────
    c12_val = ws.cell(row=12, column=3).value
    rule8_ok = close_enough(c12_val, -50000.00)
    checks.append({
        "name": "rule8_c12_payables",
        "passed": rule8_ok,
        "detail": f"Rule8: C12(应付款本月发生额) expected ~-50000, got {c12_val}"
    })

    # ── CHECK: Rule 9 - C14 = 经营利润 = 29583.54 ────────────────────────────
    c14_val = ws.cell(row=14, column=3).value
    rule9_ok = close_enough(c14_val, 29583.54)
    checks.append({
        "name": "rule9_c14_operating_profit",
        "passed": rule9_ok,
        "detail": f"Rule9: C14(当年利润本月发生额) expected ~29583.54, got {c14_val}"
    })

    # ── CHECK: Rule 10 - C15 = 0 ─────────────────────────────────────────────
    c15_val = ws.cell(row=15, column=3).value
    rule10_ok = (c15_val == 0 or c15_val is None or close_enough(c15_val, 0))
    checks.append({
        "name": "rule10_c15_undistributed_profit_zero",
        "passed": rule10_ok,
        "detail": f"Rule10: C15(未分配利润本月发生额) expected 0, got {c15_val}"
    })

    # ── CHECK: Rule 11 - Formula preservation ────────────────────────────────
    # C7 should still be a formula =D7-B7 (not a hardcoded value)
    c7_formula = ws_f.cell(row=7, column=3).value
    rule11_c7_ok = isinstance(c7_formula, str) and c7_formula.startswith("=")
    checks.append({
        "name": "rule11_c7_formula_preserved",
        "passed": rule11_c7_ok,
        "detail": f"Rule11: C7 should be formula starting with '=', got: {repr(c7_formula)}"
    })

    # C9 should be a value (not formula) since we set it in rule 6
    # C4 formula check: D4 should still be formula =B4+C4
    d4_formula = ws_f.cell(row=4, column=4).value
    rule11_d4_ok = isinstance(d4_formula, str) and d4_formula.startswith("=")
    checks.append({
        "name": "rule11_d4_formula_preserved",
        "passed": rule11_d4_ok,
        "detail": f"Rule11: D4 should be formula starting with '=', got: {repr(d4_formula)}"
    })

    # D9 should still be formula =B9+C9
    d9_formula = ws_f.cell(row=9, column=4).value
    rule11_d9_ok = isinstance(d9_formula, str) and d9_formula.startswith("=")
    checks.append({
        "name": "rule11_d9_formula_preserved",
        "passed": rule11_d9_ok,
        "detail": f"Rule11: D9 should be formula starting with '=', got: {repr(d9_formula)}"
    })

    # ── CHECK: Bank aggregation correctness (multi-row sum for 招商银行) ──────
    # The key proprietary trap: D7 must be SUM of all 招商银行 rows (2 rows), not just first
    # This is already tested by rule4 check above (228843.03 = 27780.68 + 201062.35)
    bank_sum_ok = rule4_ok
    checks.append({
        "name": "bank_multi_row_aggregation",
        "passed": bank_sum_ok,
        "detail": f"招商银行 multi-row aggregation: 27780.68 + 201062.35 = 228843.03 -> D7={d7_val}"
    })

    # ── CHECK: Non-bank/non-target rows in D column - not zeroed out ─────────
    # D6 (现金) should remain 12500 (it was a numeric value in template, not overwritten by rules)
    d6_val = ws.cell(row=6, column=4).value
    # D6 is a hardcoded number 12500.00 in source - rule 2 copies it to B6, D6 stays
    d6_ok = close_enough(d6_val, 12500.00)
    checks.append({
        "name": "non_target_cells_unchanged",
        "passed": d6_ok,
        "detail": f"D6(现金累计金额) should remain ~12500.00, got {d6_val}"
    })

    # ── CHECK: Subject names preserved (non-numeric text not changed) ─────────
    a7_val = ws.cell(row=7, column=1).value
    a7_ok = a7_val is not None and "招商" in str(a7_val)
    checks.append({
        "name": "subject_names_preserved",
        "passed": a7_ok,
        "detail": f"A7 subject name should contain '招商', got: {repr(a7_val)}"
    })

    # ── Compute score ─────────────────────────────────────────────────────────
    critical_checks = [
        "rule4_d7_zhaoShang_bank",
        "rule5_d8_jiaotong_bank",
        "rule6_c9_receivables",
        "rule7_c11_advance_receipts",
        "rule8_c12_payables",
        "rule9_c14_operating_profit",
        "rule10_c15_undistributed_profit_zero",
        "rule3_c5_fixed_assets_zero",
        "rule11_c7_formula_preserved",
        "bank_multi_row_aggregation",
    ]
    passed_checks = [c for c in checks if c["passed"]]
    critical_passed = [c for c in checks if c["name"] in critical_checks and c["passed"]]

    score = len(passed_checks) / len(checks) if checks else 0.0
    # Must pass all critical checks to be considered "passed"
    all_critical_passed = len(critical_passed) == len(critical_checks)
    overall_passed = all_critical_passed and score >= 0.75

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()