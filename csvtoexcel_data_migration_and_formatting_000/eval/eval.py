#!/usr/bin/env python3
"""Evaluation script for the csv-to-excel multi-sheet task."""

import json
import sys
import traceback
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill
except ImportError:
    print(json.dumps({
        "passed": False, "score": 0.0,
        "checks": [{"name": "import_openpyxl", "passed": False,
                    "detail": "openpyxl not installed in eval env"}]
    }))
    sys.exit(0)

def col_width_units(text):
    """Replicate the skill's column width logic."""
    w = 0
    for ch in str(text):
        w += 2 if ord(ch) > 127 else 1
    return w

def run_checks(workspace: str):
    checks = []
    ws_path = Path(workspace)

    # ── 1. Find the output Excel file ────────────────────────────────────────
    candidates = list(ws_path.rglob("quarterly_report.xlsx"))
    if not candidates:
        # also accept 季度报告 variants
        candidates = list(ws_path.rglob("*.xlsx"))

    found_file = None
    for c in candidates:
        # skip any pre-existing distractors (there are none, but be safe)
        found_file = c
        break

    file_exists = found_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found: {found_file}" if file_exists else "No .xlsx file found in workspace"
    })
    if not file_exists:
        return checks

    # ── 2. Load workbook ──────────────────────────────────────────────────────
    try:
        wb = openpyxl.load_workbook(found_file)
    except Exception as e:
        checks.append({"name": "workbook_loadable", "passed": False,
                        "detail": f"Cannot open workbook: {e}"})
        return checks
    checks.append({"name": "workbook_loadable", "passed": True, "detail": str(found_file)})

    sheet_names = wb.sheetnames

    # ── 3. Three sheets present ───────────────────────────────────────────────
    has_three = len(sheet_names) == 3
    checks.append({
        "name": "three_sheets_present",
        "passed": has_three,
        "detail": f"Sheet names found: {sheet_names}"
    })

    # ── 4. Chinese sheet names ────────────────────────────────────────────────
    expected_chinese = ["销售数据", "库存数据", "财务数据"]
    # Accept any ordering that contains all three
    all_chinese = all(name in sheet_names for name in expected_chinese)
    checks.append({
        "name": "chinese_sheet_names",
        "passed": all_chinese,
        "detail": f"Expected {expected_chinese}, got {sheet_names}"
    })

    # ── 5. GBK data decoded correctly (inventory sheet) ──────────────────────
    inv_sheet = None
    for name in sheet_names:
        if "库存" in name:
            inv_sheet = wb[name]
            break

    if inv_sheet is None:
        checks.append({"name": "gbk_encoding_correct", "passed": False,
                        "detail": "Inventory sheet not found"})
    else:
        # Row 1 should have '商品名称', row 2 col2 should be '蓝牙耳机'
        header_vals = [str(c.value) if c.value else "" for c in inv_sheet[1]]
        gbk_ok = "商品名称" in header_vals
        checks.append({
            "name": "gbk_encoding_correct",
            "passed": gbk_ok,
            "detail": f"Header row of inventory sheet: {header_vals}"
        })

    # ── 6. Header row formatting: bold + blue fill + white font ──────────────
    # Check on the sales sheet (first data sheet)
    sales_sheet = None
    for name in sheet_names:
        if "销售" in name:
            sales_sheet = wb[name]
            break

    if sales_sheet is None:
        checks.append({"name": "header_formatting_bold_blue", "passed": False,
                        "detail": "Sales sheet not found for formatting check"})
        checks.append({"name": "header_font_white", "passed": False,
                        "detail": "Sales sheet not found"})
    else:
        h1 = sales_sheet.cell(1, 1)
        is_bold = h1.font and h1.font.bold
        fill_ok = (h1.fill and h1.fill.fgColor and
                   h1.fill.fgColor.rgb and
                   h1.fill.fgColor.rgb.upper().endswith("4472C4"))
        checks.append({
            "name": "header_formatting_bold_blue",
            "passed": bool(is_bold and fill_ok),
            "detail": f"bold={is_bold}, fill_rgb={h1.fill.fgColor.rgb if h1.fill and h1.fill.fgColor else 'N/A'}"
        })
        font_white = (h1.font and h1.font.color and
                      h1.font.color.rgb and
                      h1.font.color.rgb.upper().endswith("FFFFFF"))
        checks.append({
            "name": "header_font_white",
            "passed": bool(font_white),
            "detail": f"font color rgb={h1.font.color.rgb if h1.font and h1.font.color else 'N/A'}"
        })

    # ── 7. Borders on data cells ──────────────────────────────────────────────
    if sales_sheet:
        data_cell = sales_sheet.cell(2, 1)
        border = data_cell.border
        has_borders = (border and border.left and border.left.style == "thin" and
                       border.right and border.right.style == "thin" and
                       border.top and border.top.style == "thin" and
                       border.bottom and border.bottom.style == "thin")
        checks.append({
            "name": "thin_borders_on_data",
            "passed": bool(has_borders),
            "detail": (f"left={border.left.style if border and border.left else 'N/A'}, "
                       f"right={border.right.style if border and border.right else 'N/A'}")
        })
    else:
        checks.append({"name": "thin_borders_on_data", "passed": False,
                        "detail": "Sales sheet not found"})

    # ── 8. Frozen pane at A2 ─────────────────────────────────────────────────
    if sales_sheet:
        freeze = sales_sheet.freeze_panes
        freeze_ok = (str(freeze) == "A2")
        checks.append({
            "name": "frozen_panes_A2",
            "passed": freeze_ok,
            "detail": f"freeze_panes='{freeze}'"
        })
    else:
        checks.append({"name": "frozen_panes_A2", "passed": False,
                        "detail": "Sales sheet not found"})

    # ── 9. Column width: Chinese char counting (2 units) + max 50 + 2 pad ────
    if sales_sheet:
        from openpyxl.utils import get_column_letter
        # Column 2 header is '产品名称' (4 Chinese chars = 8 units) + 2 pad = 10
        # data values like '蓝牙耳机' = 8 units, '智能手表' = 8 units, '平板电脑支架' = 12 units
        # expected max for col2 = max(col_width('产品名称'), col_width('蓝牙耳机'), ..., col_width('平板电脑支架'))
        # '平板电脑支架' = 6 chars * 2 = 12 units; header '产品名称' = 8 units => max=12, +2=14
        col2_letter = get_column_letter(2)
        col2_width = sales_sheet.column_dimensions[col2_letter].width
        # Expected: min(12+2, 50) = 14
        width_ok = (col2_width is not None and abs(col2_width - 14.0) < 1.5)
        checks.append({
            "name": "column_width_chinese_2units",
            "passed": width_ok,
            "detail": (f"Col 2 ('产品名称'/'平板电脑支架') expected ~14.0, "
                       f"got {col2_width}")
        })
    else:
        checks.append({"name": "column_width_chinese_2units", "passed": False,
                        "detail": "Sales sheet not found"})

    # ── 10. Finance sheet UTF-8-SIG data integrity ────────────────────────────
    fin_sheet = None
    for name in sheet_names:
        if "财务" in name:
            fin_sheet = wb[name]
            break

    if fin_sheet is None:
        checks.append({"name": "finance_data_integrity", "passed": False,
                        "detail": "Finance sheet not found"})
    else:
        # Header row col1 should be '费用类别'
        fin_header = fin_sheet.cell(1, 1).value
        fin_ok = (fin_header == "费用类别")
        checks.append({
            "name": "finance_data_integrity",
            "passed": fin_ok,
            "detail": f"Finance sheet cell A1='{fin_header}', expected '费用类别'"
        })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks = run_checks(workspace)
    except Exception:
        checks = [{"name": "eval_crash", "passed": False,
                   "detail": traceback.format_exc()}]

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall = (passed_count == total)

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()