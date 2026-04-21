import json
import os
import sys
from pathlib import Path
import subprocess

def main():
    workspace = Path(sys.argv[1])
    checks = []
    
    # Check if the Excel file exists with correct name
    excel_file = workspace / 'techflow_model.xlsx'
    if not excel_file.exists():
        checks.append({"name": "File Creation", "passed": False, "detail": "techflow_model.xlsx not found"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    checks.append({"name": "File Creation", "passed": True, "detail": "techflow_model.xlsx created successfully"})
    
    try:
        from openpyxl import load_workbook
        
        # Load workbook and check worksheets
        wb = load_workbook(excel_file, data_only=False)
        expected_sheets = ['Income Statement', 'Balance Sheet', 'Cash Flow']
        actual_sheets = wb.sheetnames
        
        sheets_found = sum(1 for sheet in expected_sheets if any(sheet.lower() in actual.lower() for actual in actual_sheets))
        checks.append({"name": "Worksheet Structure", "passed": sheets_found >= 3, "detail": f"Found {sheets_found}/3 required worksheets"})
        
        # Find income statement sheet
        income_sheet = None
        for sheet_name in wb.sheetnames:
            if 'income' in sheet_name.lower():
                income_sheet = wb[sheet_name]
                break
        
        if income_sheet is None:
            checks.append({"name": "Income Statement Data", "passed": False, "detail": "Income Statement sheet not found"})
        else:
            # Check for years 2024-2028
            years_found = 0
            revenue_found = False
            base_revenue_correct = False
            
            for row in income_sheet.iter_rows(max_row=20, max_col=10):
                for cell in row:
                    if cell.value and str(cell.value).strip() in ['2024', '2025', '2026', '2027', '2028']:
                        years_found += 1
                    if cell.value and 'revenue' in str(cell.value).lower():
                        revenue_found = True
                        # Check if base revenue is around $10M
                        # Support multiple formats: 10000000, 10M, $10M, 10,000,000, formulas
                        revenue_row = cell.row
                        for col in range(cell.column + 1, cell.column + 6):
                            revenue_cell = income_sheet.cell(revenue_row, col)
                            val = revenue_cell.value
                            if val is not None:
                                # Direct numeric match
                                if isinstance(val, (int, float)) and abs(val - 10000000) < 100000:
                                    base_revenue_correct = True
                                    break
                                # String format match (e.g., "$10M", "10,000,000", "10M")
                                if isinstance(val, str):
                                    val_clean = val.replace(',', '').replace('$', '').replace(' ', '').lower()
                                    if 'm' in val_clean:
                                        # Format like "10m" means 10 million
                                        try:
                                            num = float(val_clean.replace('m', ''))
                                            if abs(num - 10) < 0.1:
                                                base_revenue_correct = True
                                                break
                                        except:
                                            pass
                                    else:
                                        try:
                                            num = float(val_clean)
                                            if abs(num - 10000000) < 100000 or abs(num - 10) < 0.1:
                                                base_revenue_correct = True
                                                break
                                        except:
                                            pass
                                # Formula that might evaluate to 10M
                                if isinstance(val, str) and val.startswith('='):
                                    if '10000000' in val or '10*million' in val.lower() or '10*1000000' in val:
                                        base_revenue_correct = True
                                        break
            
            checks.append({"name": "Year Headers", "passed": years_found >= 5, "detail": f"Found {years_found}/5 year headers"})
            checks.append({"name": "Revenue Line", "passed": revenue_found, "detail": "Revenue line found" if revenue_found else "Revenue line not found"})
            checks.append({"name": "Base Revenue", "passed": base_revenue_correct, "detail": "2024 revenue ~$10M" if base_revenue_correct else "2024 revenue not $10M"})
        
        # Check for formulas vs hardcoded values
        formula_count = 0
        total_numeric_cells = 0
        
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value and isinstance(cell.value, str) and cell.value.startswith('='):
                        formula_count += 1
                    elif cell.value and isinstance(cell.value, (int, float)):
                        total_numeric_cells += 1
        
        formula_ratio = formula_count / max(total_numeric_cells, 1) if total_numeric_cells > 0 else 0
        checks.append({"name": "Formula Usage", "passed": formula_ratio > 0.3, "detail": f"Formula ratio: {formula_ratio:.2f}"})
        
        # Check for proper formatting (basic check for currency and text years)
        formatting_good = False
        text_years_found = False
        
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            for row in sheet.iter_rows(max_row=10, max_col=10):
                for cell in row:
                    if cell.value and str(cell.value).strip() in ['2024', '2025', '2026', '2027', '2028']:
                        text_years_found = True
                    if cell.number_format and ('$' in cell.number_format or '#,##0' in cell.number_format):
                        formatting_good = True
        
        checks.append({"name": "Text Year Format", "passed": text_years_found, "detail": "Years formatted as text" if text_years_found else "Years not formatted as text"})
        checks.append({"name": "Currency Formatting", "passed": formatting_good, "detail": "Currency formatting found" if formatting_good else "Currency formatting not found"})
        
        # Run recalculation to check for formula errors
        recalc_script = workspace.parent / 'scripts' / 'recalc.py'
        if recalc_script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(recalc_script), str(excel_file)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=workspace
                )
                if result.returncode == 0:
                    recalc_data = json.loads(result.stdout)
                    no_errors = recalc_data.get('total_errors', 1) == 0
                    checks.append({"name": "Formula Errors", "passed": no_errors, "detail": f"Errors: {recalc_data.get('total_errors', 'unknown')}"})
                else:
                    checks.append({"name": "Formula Errors", "passed": False, "detail": "Recalculation failed"})
            except Exception as e:
                checks.append({"name": "Formula Errors", "passed": False, "detail": f"Recalc error: {str(e)[:100]}"})
        else:
            checks.append({"name": "Formula Errors", "passed": True, "detail": "Recalc script not available"})
        
        # Check for summary metrics
        summary_found = False
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value and isinstance(cell.value, str):
                        cell_text = cell.value.lower()
                        if any(term in cell_text for term in ['cagr', 'ebitda margin', 'net income margin', 'summary']):
                            summary_found = True
                            break
        
        checks.append({"name": "Summary Metrics", "passed": summary_found, "detail": "Summary metrics found" if summary_found else "Summary metrics not found"})
        
        wb.close()
        
    except Exception as e:
        checks.append({"name": "File Analysis", "passed": False, "detail": f"Error analyzing file: {str(e)[:100]}"})
    
    # Calculate final score
    passed_count = sum(1 for check in checks if check['passed'])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    passed = score >= 0.8
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()