#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import time
from pathlib import Path

def check_file_exists(workspace_dir, filename):
    """Check if a file exists in the workspace."""
    file_path = Path(workspace_dir) / filename
    return file_path.exists(), str(file_path)

def check_playwright_script_structure(workspace_dir):
    """Check if there's a valid Playwright automation script."""
    # Look for Python files that might be the automation script
    py_files = list(Path(workspace_dir).glob('*.py'))
    
    automation_files = []
    for py_file in py_files:
        if py_file.name in ['gen_inputs_script.py', 'eval_script.py']:
            continue
        
        try:
            content = py_file.read_text()
            # Check for Playwright imports and basic structure
            if ('playwright' in content and 
                ('sync_playwright' in content or 'async_playwright' in content) and
                'browser' in content and
                'page' in content):
                automation_files.append(py_file)
        except Exception:
            continue
    
    return len(automation_files) > 0, automation_files

def run_automation_test(workspace_dir):
    """Run the automation script and check if it executes successfully."""
    # Find automation script
    has_script, script_files = check_playwright_script_structure(workspace_dir)
    if not has_script:
        return False, "No valid Playwright automation script found"
    
    script_file = script_files[0]
    
    try:
        # Use the with_server.py script to run the test
        with_server_script = Path(workspace_dir) / 'scripts' / 'with_server.py'
        
        if not with_server_script.exists():
            # Check if user created their own server management
            result = subprocess.run(
                [sys.executable, str(script_file)],
                cwd=workspace_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
        else:
            # Use the provided with_server.py helper
            result = subprocess.run([
                sys.executable, str(with_server_script),
                '--server', 'cd todo-app && npm start',
                '--port', '3000',
                '--timeout', '45',
                '--', sys.executable, str(script_file.name)
            ], cwd=workspace_dir, capture_output=True, text=True, timeout=120)
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        return success, output
    
    except subprocess.TimeoutExpired:
        return False, "Automation script timed out"
    except Exception as e:
        return False, f"Error running automation script: {str(e)}"

def check_automation_content(workspace_dir):
    """Check if the automation script contains expected testing operations."""
    has_script, script_files = check_playwright_script_structure(workspace_dir)
    if not has_script:
        return False, "No automation script found"
    
    script_file = script_files[0]
    content = script_file.read_text().lower()
    
    checks = {
        'navigates_to_localhost': 'localhost:3000' in content or 'localhost' in content,
        'waits_for_load': 'wait_for_load_state' in content or 'networkidle' in content,
        'interacts_with_input': ('input' in content or 'todo-input' in content) and 'fill' in content,
        'clicks_add_button': ('add' in content and 'click' in content) or 'add-button' in content,
        'checks_todo_list': 'todo-list' in content or ('locator' in content and 'li' in content),
        'tests_complete_functionality': 'complete' in content or 'toggle' in content,
        'tests_delete_functionality': 'delete' in content,
        'takes_screenshot_or_checks_content': 'screenshot' in content or 'text_content' in content or 'inner_text' in content
    }
    
    passed_checks = sum(checks.values())
    total_checks = len(checks)
    
    return passed_checks >= 5, f"Passed {passed_checks}/{total_checks} automation checks: {checks}"

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        return
    
    workspace_dir = sys.argv[1]
    checks = []
    
    # Check 1: Todo app exists
    app_exists, app_path = check_file_exists(workspace_dir, 'todo-app/src/App.js')
    checks.append({
        "name": "todo_app_exists", 
        "passed": app_exists, 
        "detail": f"Todo app found at {app_path}" if app_exists else "Todo app not found"
    })
    
    # Check 2: Playwright automation script exists
    has_automation, script_files = check_playwright_script_structure(workspace_dir)
    checks.append({
        "name": "automation_script_exists", 
        "passed": has_automation, 
        "detail": f"Found automation scripts: {[str(f) for f in script_files]}" if has_automation else "No valid Playwright automation script found"
    })
    
    # Check 3: Automation script has proper testing content
    if has_automation:
        content_check, content_detail = check_automation_content(workspace_dir)
        checks.append({
            "name": "automation_content_quality", 
            "passed": content_check, 
            "detail": content_detail
        })
    else:
        checks.append({
            "name": "automation_content_quality", 
            "passed": False, 
            "detail": "Cannot check content - no automation script found"
        })
    
    # Check 4: Try to run the automation (if possible)
    if has_automation and app_exists:
        run_success, run_output = run_automation_test(workspace_dir)
        checks.append({
            "name": "automation_execution", 
            "passed": run_success, 
            "detail": f"Execution successful" if run_success else f"Execution failed: {run_output[:200]}..."
        })
    else:
        checks.append({
            "name": "automation_execution", 
            "passed": False, 
            "detail": "Cannot run automation - missing prerequisites"
        })
    
    # Calculate score
    passed_count = sum(1 for check in checks if check["passed"])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    overall_passed = score >= 0.75
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
