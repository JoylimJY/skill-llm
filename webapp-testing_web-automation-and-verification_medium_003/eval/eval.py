#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)
    
    # Check 1: test_todo_app.py exists
    script_path = workspace / 'test_todo_app.py'
    check1 = {
        'name': 'Script file exists',
        'passed': script_path.exists(),
        'detail': 'test_todo_app.py found' if script_path.exists() else 'test_todo_app.py not found'
    }
    checks.append(check1)
    
    # Check 2: initial_state.png exists
    initial_png = workspace / 'initial_state.png'
    check2 = {
        'name': 'Initial screenshot captured',
        'passed': initial_png.exists(),
        'detail': 'initial_state.png found' if initial_png.exists() else 'initial_state.png not found'
    }
    checks.append(check2)
    
    # Check 3: final_state.png exists
    final_png = workspace / 'final_state.png'
    check3 = {
        'name': 'Final screenshot captured',
        'passed': final_png.exists(),
        'detail': 'final_state.png found' if final_png.exists() else 'final_state.png not found'
    }
    checks.append(check3)
    
    # Check 4: test_results.json exists and has correct structure
    results_json = workspace / 'test_results.json'
    check4_passed = False
    check4_detail = 'test_results.json not found'
    
    if results_json.exists():
        try:
            with open(results_json, 'r') as f:
                data = json.load(f)
            
            has_total = data.get('total_items') == 3
            has_completed = data.get('completed_items') == 1
            has_screenshots = data.get('screenshots_taken') == 2
            
            check4_passed = has_total and has_completed and has_screenshots
            check4_detail = f"total_items={data.get('total_items')}, completed_items={data.get('completed_items')}, screenshots_taken={data.get('screenshots_taken')}"
        except (json.JSONDecodeError, TypeError) as e:
            check4_detail = f'Invalid JSON: {str(e)}'
    
    check4 = {
        'name': 'Test results JSON valid',
        'passed': check4_passed,
        'detail': check4_detail
    }
    checks.append(check4)
    
    # Check 5: Script contains Playwright imports and key operations
    check5_passed = False
    check5_detail = 'Script not readable'
    
    if script_path.exists():
        try:
            with open(script_path, 'r') as f:
                script_content = f.read().lower()
            
            has_playwright = 'playwright' in script_content
            has_goto = 'goto' in script_content and '5173' in script_content
            has_screenshot = 'screenshot' in script_content
            has_json_dump = 'json' in script_content and 'dump' in script_content
            
            check5_passed = has_playwright and has_goto and has_screenshot and has_json_dump
            check5_detail = f"playwright={has_playwright}, goto_5173={has_goto}, screenshot={has_screenshot}, json_dump={has_json_dump}"
        except Exception as e:
            check5_detail = f'Error reading script: {str(e)}'
    
    check5 = {
        'name': 'Script contains required operations',
        'passed': check5_passed,
        'detail': check5_detail
    }
    checks.append(check5)
    
    # Calculate score
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks)
    overall_passed = score == 1.0
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    result = evaluate(workspace)
    print(json.dumps(result))
