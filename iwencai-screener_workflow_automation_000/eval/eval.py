#!/usr/bin/env python3
"""
Evaluation script for iwencai-screener task.
Checks:
1. An Excel file matching 选股结果_YYYYMMDD_HHMMSS.xlsx was generated
2. The Excel file has 3-5 sheets (core directions, not too many/few)
3. Each sheet has at most 5 data rows (stock rows, excluding header)
4. Each sheet has at least 1 data row
5. Sheet names are meaningful (not empty/default)
6. The file was generated using generate_stock_excel.py logic (openpyxl format, proper headers)
7. The content is related to the EV charging infrastructure domain
"""

import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    
    workspace = Path(workspace_dir)
    
    # =========================================================
    # CHECK 1: Excel file with correct naming convention exists
    # =========================================================
    excel_pattern = re.compile(r'^选股结果_\d{8}_\d{6}\.xlsx$')
    
    found_excel_files = []
    try:
        # Search recursively, but exclude the old distractor file
        for f in workspace.rglob("*.xlsx"):
            if excel_pattern.match(f.name):
                # Exclude the pre-existing distractor file
                if "20240101_120000" not in f.name:
                    found_excel_files.append(f)
    except Exception as e:
        checks.append({
            "name": "excel_file_naming_convention",
            "passed": False,
            "detail": f"Error searching for Excel files: {e}"
        })
    
    if not found_excel_files:
        checks.append({
            "name": "excel_file_naming_convention",
            "passed": False,
            "detail": "No Excel file matching '选股结果_YYYYMMDD_HHMMSS.xlsx' pattern found (excluding the pre-existing distractor). Agent must generate a new file using generate_stock_excel.py."
        })
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    # Use the most recently created matching file
    target_excel = sorted(found_excel_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    checks.append({
        "name": "excel_file_naming_convention",
        "passed": True,
        "detail": f"Found Excel file: {target_excel.name} at {target_excel}"
    })
    total_score += 0.15
    
    # =========================================================
    # CHECK 2: Excel file is valid and readable
    # =========================================================
    try:
        import openpyxl
        wb = openpyxl.load_workbook(target_excel)
        sheets = wb.sheetnames
        checks.append({
            "name": "excel_file_valid",
            "passed": True,
            "detail": f"Excel file is valid. Sheets: {sheets}"
        })
        total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "excel_file_valid",
            "passed": False,
            "detail": f"Excel file could not be opened: {e}"
        })
        return {
            "passed": False,
            "score": total_score,
            "checks": checks
        }
    
    # =========================================================
    # CHECK 3: Sheet count is 3-5 (SKILL.md: 聚焦3-5个方向, 最多5个Sheet)
    # =========================================================
    num_sheets = len(sheets)
    sheet_count_ok = 3 <= num_sheets <= 5
    checks.append({
        "name": "sheet_count_3_to_5",
        "passed": sheet_count_ok,
        "detail": f"Excel has {num_sheets} sheets ({sheets}). SKILL.md requires 3-5 core directions, each with its own sheet. {'PASS' if sheet_count_ok else 'FAIL: must have 3-5 sheets.'}"
    })
    if sheet_count_ok:
        total_score += 0.20
    
    # =========================================================
    # CHECK 4: Each sheet has at most 5 data rows (SKILL.md: 每个方向最多5只股票)
    # =========================================================
    all_sheets_row_ok = True
    sheet_row_details = []
    sheets_with_data = 0
    
    for sheet_name in sheets:
        try:
            ws = wb[sheet_name]
            # Count data rows (excluding header row 1)
            max_row = ws.max_row
            # Header is row 1, data starts at row 2
            data_rows = max_row - 1 if max_row > 1 else 0
            
            # Check if sheet actually has content (not just placeholder)
            has_real_data = False
            if max_row >= 2:
                for row in ws.iter_rows(min_row=2, max_row=min(max_row, 6), values_only=True):
                    if any(cell is not None and str(cell).strip() for cell in row):
                        has_real_data = True
                        break
            
            if has_real_data:
                sheets_with_data += 1
            
            if data_rows > 5:
                all_sheets_row_ok = False
                sheet_row_details.append(f"Sheet '{sheet_name}': {data_rows} rows (EXCEEDS 5-stock limit)")
            else:
                sheet_row_details.append(f"Sheet '{sheet_name}': {data_rows} data rows (OK)")
        except Exception as e:
            sheet_row_details.append(f"Sheet '{sheet_name}': Error reading - {e}")
            all_sheets_row_ok = False
    
    checks.append({
        "name": "max_5_stocks_per_sheet",
        "passed": all_sheets_row_ok,
        "detail": "; ".join(sheet_row_details)
    })
    if all_sheets_row_ok:
        total_score += 0.20
    
    # =========================================================
    # CHECK 5: All sheets have at least 1 data row (non-empty)
    # =========================================================
    all_non_empty = sheets_with_data == num_sheets
    checks.append({
        "name": "all_sheets_have_data",
        "passed": all_non_empty,
        "detail": f"{sheets_with_data}/{num_sheets} sheets have actual stock data. All sheets must have at least 1 stock entry."
    })
    if all_non_empty:
        total_score += 0.10
    
    # =========================================================
    # CHECK 6: Sheet names are domain-relevant (EV charging sector)
    # =========================================================
    domain_keywords = [
        "充电", "储能", "光伏", "电力", "新能源", "光储", "配电", "运营",
        "电网", "电气", "充电桩", "充电模块", "汽车", "电池", "功率"
    ]
    relevant_sheets = []
    irrelevant_sheets = []
    
    for sname in sheets:
        if any(kw in sname for kw in domain_keywords):
            relevant_sheets.append(sname)
        else:
            irrelevant_sheets.append(sname)
    
    # At least 2/3 of sheets should be domain-relevant
    relevance_ratio = len(relevant_sheets) / num_sheets if num_sheets > 0 else 0
    domain_relevant = relevance_ratio >= 0.5
    
    checks.append({
        "name": "sheet_names_domain_relevant",
        "passed": domain_relevant,
        "detail": f"Relevant sheets: {relevant_sheets}; Irrelevant sheets: {irrelevant_sheets}. {len(relevant_sheets)}/{num_sheets} sheets have domain-relevant names."
    })
    if domain_relevant:
        total_score += 0.15
    
    # =========================================================
    # CHECK 7: Stock data has required fields (代码, 名称 at minimum)
    # =========================================================
    fields_check_passed = False
    field_details = []
    
    for sheet_name in sheets[:3]:  # Check first 3 sheets
        try:
            ws = wb[sheet_name]
            if ws.max_row < 1:
                continue
            # Get header row
            header_row = [cell.value for cell in ws[1] if cell.value is not None]
            if header_row:
                has_code = any("代码" in str(h) or "code" in str(h).lower() for h in header_row)
                has_name = any("名称" in str(h) or "name" in str(h).lower() or "股票" in str(h) for h in header_row)
                field_details.append(f"Sheet '{sheet_name}' headers: {header_row[:6]} | 代码:{has_code} 名称:{has_name}")
                if has_code or has_name:
                    fields_check_passed = True
        except Exception as e:
            field_details.append(f"Sheet '{sheet_name}': Error - {e}")
    
    checks.append({
        "name": "stock_data_has_required_fields",
        "passed": fields_check_passed,
        "detail": "; ".join(field_details) if field_details else "No headers found in sheets"
    })
    if fields_check_passed:
        total_score += 0.10
    
    # =========================================================
    # FINAL VERDICT
    # =========================================================
    critical_checks = ["excel_file_naming_convention", "excel_file_valid", "sheet_count_3_to_5", "max_5_stocks_per_sheet"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    passed = critical_passed and total_score >= 0.50
    
    return {
        "passed": passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "setup", "passed": False, "detail": "No workspace directory provided"}]}))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))