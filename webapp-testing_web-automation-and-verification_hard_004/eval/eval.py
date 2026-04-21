#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Check 1: test_webapp.py exists
    script_path = Path(workspace_dir) / 'test_webapp.py'
    check1 = {
        'name': 'Script file exists',
        'passed': script_path.exists(),
        'detail': f'test_webapp.py found at {script_path}' if script_path.exists() else 'test_webapp.py not found'
    }
    checks.append(check1)
    
    if not check1['passed']:
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    # Check 2: Script is valid Python
    try:
        with open(script_path, 'r') as f:
            script_content = f.read()
        compile(script_content, str(script_path), 'exec')
        check2 = {'name': 'Valid Python syntax', 'passed': True, 'detail': 'Script compiles without syntax errors'}
    except SyntaxError as e:
        check2 = {'name': 'Valid Python syntax', 'passed': False, 'detail': f'Syntax error: {str(e)}'}
    checks.append(check2)
    
    # Check 3: Uses sync_playwright
    check3 = {
        'name': 'Uses sync_playwright',
        'passed': 'sync_playwright' in script_content,
        'detail': 'sync_playwright import found' if 'sync_playwright' in script_content else 'sync_playwright not imported'
    }
    checks.append(check3)
    
    # Check 4: Navigates to localhost:5173
    check4 = {
        'name': 'Navigates to correct URL',
        'passed': 'localhost:5173' in script_content or '5173' in script_content,
        'detail': 'URL contains localhost:5173' if ('localhost:5173' in script_content or '5173' in script_content) else 'Correct URL not found'
    }
    checks.append(check4)
    
    # Check 5: Waits for networkidle
    check5 = {
        'name': 'Waits for network idle',
        'passed': 'networkidle' in script_content,
        'detail': 'networkidle wait found' if 'networkidle' in script_content else 'networkidle wait not found'
    }
    checks.append(check5)
    
    # Check 6: Handles login
    check6 = {
        'name': 'Handles login interaction',
        'passed': any(keyword in script_content.lower() for keyword in ['username', 'password', 'login']),
        'detail': 'Login handling code found' if any(keyword in script_content.lower() for keyword in ['username', 'password', 'login']) else 'Login handling not found'
    }
    checks.append(check6)
    
    # Check 7: Interacts with table/modal
    check7 = {
        'name': 'Interacts with table and modal',
        'passed': any(keyword in script_content.lower() for keyword in ['table', 'modal', 'click', 'row']),
        'detail': 'Table/modal interaction found' if any(keyword in script_content.lower() for keyword in ['table', 'modal', 'click', 'row']) else 'Table/modal interaction not found'
    }
    checks.append(check7)
    
    # Check 8: Takes screenshot
    check8 = {
        'name': 'Takes screenshot',
        'passed': 'screenshot' in script_content,
        'detail': 'Screenshot call found' if 'screenshot' in script_content else 'Screenshot not taken'
    }
    checks.append(check8)
    
    # Check 9: Closes browser
    check9 = {
        'name': 'Closes browser',
        'passed': 'close' in script_content,
        'detail': 'Browser close call found' if 'close' in script_content else 'Browser not closed'
    }
    checks.append(check9)
    
    # Check 10: Uses appropriate selectors
    check10 = {
        'name': 'Uses descriptive selectors',
        'passed': any(keyword in script_content for keyword in ['locator', 'selector', 'text=', 'role=']),
        'detail': 'Selector methods found' if any(keyword in script_content for keyword in ['locator', 'selector', 'text=', 'role=']) else 'Selector methods not found'
    }
    checks.append(check10)
    
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks)
    overall_passed = score >= 0.8
    
    return {'passed': overall_passed, 'score': score, 'checks': checks}

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    result = evaluate(workspace)
    print(json.dumps(result))
