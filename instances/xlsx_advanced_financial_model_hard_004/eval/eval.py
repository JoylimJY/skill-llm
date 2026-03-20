import sys
import json
from pathlib import Path
from openpyxl import load_workbook
import pandas as pd

def eval_financial_model(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    
    # Check if main output file exists
    model_file = workspace / 'financial_model_complete.xlsx'
    if not model_file.exists():
        return {"passed": False, "score": 0.0, "checks": [{"name": "file_exists", "passed": False, "detail": "financial_model_complete.xlsx not found"}]}
    
    try:
        wb = load_workbook(str(model_file), data_only=False)
        wb_data = load_workbook(str(model_file), data_only=True)
        
        # Check 1: Multiple worksheets for different components
        required_sheets = ['Assumptions', 'P&L', 'Balance Sheet', 'Cash Flow', 'DCF', 'Sensitivity']
        found_sheets = []
        for sheet_name in wb.sheetnames:
            for req in required_sheets:
                if req.lower() in sheet_name.lower() or any(word in sheet_name.lower() for word in req.lower().split()):
                    found_sheets.append(req)
                    break
        
        sheet_check = len(found_sheets) >= 4
        checks.append({"name": "multiple_sheets", "passed": sheet_check, "detail": f"Found {len(found_sheets)}/6 required sheet types: {found_sheets}"})
        
        # Check 2: Revenue projections (5 years forward)
        revenue_found = False
        projection_years = 0
        
        for sheet_name in wb.sheetnames:
            ws = wb_data[sheet_name]
            for row in ws.iter_rows(values_only=True):
                if row and any(cell and 'revenue' in str(cell).lower() for cell in row[:5]):
                    # Look for years 2024-2028 in subsequent rows
                    for check_row in ws.iter_rows(values_only=True):
                        if check_row and any(cell in [2024, 2025, 2026, 2027, 2028, '2024', '2025', '2026', '2027', '2028'] for cell in check_row[:10] if cell):
                            projection_years = max(projection_years, sum(1 for cell in check_row[:10] if cell and str(cell) in ['2024', '2025', '2026', '2027', '2028']))
                            revenue_found = True
                            break
                    break
        
        revenue_check = revenue_found and projection_years >= 4
        checks.append({"name": "revenue_projections", "passed": revenue_check, "detail": f"Revenue projections found: {revenue_found}, projection years: {projection_years}"})
        
        # Check 3: Formulas (not hardcoded values)
        formula_count = 0
        total_data_cells = 0
        
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            for row in ws.iter_rows():
                for cell in row:
                    if cell.value is not None:
                        total_data_cells += 1
                        if isinstance(cell.value, str) and cell.value.startswith('='):
                            formula_count += 1
        
        formula_ratio = formula_count / max(total_data_cells, 1)
        formula_check = formula_count >= 50 and formula_ratio >= 0.2
        checks.append({"name": "formulas_used", "passed": formula_check, "detail": f"Found {formula_count} formulas in {total_data_cells} data cells (ratio: {formula_ratio:.2f})"})
        
        # Check 4: DCF valuation components
        dcf_components = ['wacc', 'terminal', 'npv', 'enterprise value', 'equity value']
        dcf_found = 0
        
        for sheet_name in wb.sheetnames:
            ws = wb_data[sheet_name]
            sheet_text = ' '.join([str(cell.value).lower() for row in ws.iter_rows(values_only=True) for cell in row if cell is not None])
            for component in dcf_components:
                if component in sheet_text:
                    dcf_found += 1
                    break
        
        dcf_check = dcf_found >= 3
        checks.append({"name": "dcf_components", "passed": dcf_check, "detail": f"Found {dcf_found}/5 DCF components"})
        
        # Check 5: Sensitivity analysis
        sensitivity_found = False
        growth_ranges = False
        
        for sheet_name in wb.sheetnames:
            ws = wb_data[sheet_name]
            sheet_text = ' '.join([str(cell.value).lower() for row in ws.iter_rows(values_only=True) for cell in row if cell is not None])
            if 'sensitivity' in sheet_text or 'scenario' in sheet_text:
                sensitivity_found = True
                # Look for percentage values in reasonable ranges
                for row in ws.iter_rows(values_only=True):
                    for cell in row:
                        if isinstance(cell, (int, float)):
                            if 0.15 <= cell <= 0.25 or 0.02 <= cell <= 0.04 or 15 <= cell <= 25:
                                growth_ranges = True
                                break
                    if growth_ranges:
                        break
                break
        
        sensitivity_check = sensitivity_found and growth_ranges
        checks.append({"name": "sensitivity_analysis", "passed": sensitivity_check, "detail": f"Sensitivity analysis found: {sensitivity_found}, growth ranges: {growth_ranges}"})
        
        # Check 6: Three statement linking
        statement_links = 0
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            for row in ws.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str) and cell.value.startswith('='):
                        if '!' in cell.value:  # Cross-sheet reference
                            statement_links += 1
        
        linking_check = statement_links >= 10
        checks.append({"name": "statement_linking", "passed": linking_check, "detail": f"Found {statement_links} cross-sheet formula links"})
        
        # Check 7: ARR-driven revenue model
        arr_driven = False
        for sheet_name in wb.sheetnames:
            ws = wb_data[sheet_name]
            sheet_text = ' '.join([str(cell.value).lower() for row in ws.iter_rows(values_only=True) for cell in row if cell is not None])
            if 'arr' in sheet_text and ('churn' in sheet_text or 'customer' in sheet_text):
                arr_driven = True
                break
        
        checks.append({"name": "arr_driven_model", "passed": arr_driven, "detail": f"ARR-driven revenue model found: {arr_driven}"})
        
        wb.close()
        wb_data.close()
        
        passed_checks = sum(1 for check in checks if check['passed'])
        total_checks = len(checks)
        score = passed_checks / total_checks
        overall_passed = score >= 0.7
        
        return {
            "passed": overall_passed,
            "score": score,
            "checks": checks
        }
        
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_processing", "passed": False, "detail": f"Error processing file: {str(e)}"}]
        }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: python eval.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = eval_financial_model(sys.argv[1])
    print(json.dumps(result))