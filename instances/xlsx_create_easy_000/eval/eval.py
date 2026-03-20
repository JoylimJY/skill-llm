#!/usr/bin/env python3

import json
import sys
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook

def eval_expense_tracker(workspace_dir):
    workspace = Path(workspace_dir)
    expected_file = workspace / 'expenses_jan2024.xlsx'
    
    checks = []
    
    # Check if file exists
    file_exists = expected_file.exists()
    checks.append({
        'name': 'File exists',
        'passed': file_exists,
        'detail': f'File expenses_jan2024.xlsx exists: {file_exists}'
    })
    
    if not file_exists:
        return {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
    
    try:
        # Load workbook to check structure
        wb = load_workbook(str(expected_file), data_only=True)
        
        # Check if workbook has at least one sheet
        has_sheets = len(wb.sheetnames) > 0
        checks.append({
            'name': 'Has worksheets',
            'passed': has_sheets,
            'detail': f'Workbook has {len(wb.sheetnames)} sheet(s)'
        })
        
        if not has_sheets:
            wb.close()
            return {
                'passed': False,
                'score': 0.2,
                'checks': checks
            }
        
        # Get the first sheet
        ws = wb.active
        
        # Check for expense categories
        expense_categories = ['Food', 'Transport', 'Entertainment', 'Utilities']
        found_categories = 0
        
        # Scan for category names in the sheet
        category_found = {cat.lower(): False for cat in expense_categories}
        
        for row in ws.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    cell_lower = cell.value.lower()
                    for cat in expense_categories:
                        if cat.lower() in cell_lower:
                            category_found[cat.lower()] = True
        
        found_categories = sum(category_found.values())
        
        checks.append({
            'name': 'Has expense categories',
            'passed': found_categories >= 3,
            'detail': f'Found {found_categories} of 4 expected categories (Food, Transport, Entertainment, Utilities)'
        })
        
        # Check for numeric data (amounts)
        numeric_values = 0
        for row in ws.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, (int, float)) and cell.value > 0:
                    numeric_values += 1
        
        has_numeric_data = numeric_values >= 5
        checks.append({
            'name': 'Has numeric expense data',
            'passed': has_numeric_data,
            'detail': f'Found {numeric_values} numeric values (expenses)'
        })
        
        # Check for totals (look for SUM formulas or total-like labels)
        wb_formulas = load_workbook(str(expected_file), data_only=False)
        ws_formulas = wb_formulas.active
        
        has_formulas = False
        sum_formulas = 0
        
        for row in ws_formulas.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    if cell.value.startswith('='):
                        has_formulas = True
                        if 'SUM' in cell.value.upper():
                            sum_formulas += 1
        
        wb_formulas.close()
        
        checks.append({
            'name': 'Has formulas/totals',
            'passed': has_formulas,
            'detail': f'Has formulas: {has_formulas}, SUM formulas: {sum_formulas}'
        })
        
        # Check for January 2024 reference
        has_date_reference = False
        for row in ws.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    cell_lower = cell.value.lower()
                    if ('january' in cell_lower or 'jan' in cell_lower) and '2024' in cell_lower:
                        has_date_reference = True
                        break
            if has_date_reference:
                break
        
        checks.append({
            'name': 'Has January 2024 reference',
            'passed': has_date_reference,
            'detail': f'Contains January 2024 reference: {has_date_reference}'
        })
        
        wb.close()
        
        # Calculate score
        passed_checks = sum(1 for check in checks if check['passed'])
        total_checks = len(checks)
        score = passed_checks / total_checks
        
        # Must pass basic requirements
        basic_passed = (file_exists and has_sheets and found_categories >= 2 and has_numeric_data)
        
        return {
            'passed': basic_passed and score >= 0.7,
            'score': score,
            'checks': checks
        }
        
    except Exception as e:
        checks.append({
            'name': 'File processing',
            'passed': False,
            'detail': f'Error processing Excel file: {str(e)}'
        })
        
        return {
            'passed': False,
            'score': 0.1 if file_exists else 0.0,
            'checks': checks
        }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_dir>')
        sys.exit(1)
    
    result = eval_expense_tracker(sys.argv[1])
    print(json.dumps(result, indent=2))