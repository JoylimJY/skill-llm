import sys
import os
import json
import re
from pathlib import Path

def check_file_exists(filepath, name):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    return {
        "name": f"File exists: {name}",
        "passed": exists,
        "detail": f"File {filepath} {'exists' if exists else 'not found'}"
    }

def check_test_script_content(filepath):
    """Check if test script contains required Playwright functionality"""
    if not os.path.exists(filepath):
        return {
            "name": "Test script contains Playwright automation",
            "passed": False,
            "detail": "Test script file not found"
        }
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    required_patterns = [
        r'from playwright\.sync_api import sync_playwright',
        r'page\.goto\(["\']http://localhost:3000["\']\)',
        r'page\.wait_for_load_state\(["\']networkidle["\']\)',
        r'screenshot\(',
    ]
    
    missing_patterns = []
    for pattern in required_patterns:
        if not re.search(pattern, content):
            missing_patterns.append(pattern)
    
    # Check for todo-specific automation
    todo_patterns = [
        r'todo.input|Add.*[Tt]odo|add.*button',  # Adding todos
        r'checkbox|toggle|complete',  # Completing todos
        r'delete|remove',  # Deleting todos
    ]
    
    todo_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in todo_patterns)
    
    passed = len(missing_patterns) == 0 and todo_found
    
    detail = "Test script looks good"
    if missing_patterns:
        detail = f"Missing required patterns: {missing_patterns}"
    elif not todo_found:
        detail = "Missing todo-specific automation (add/complete/delete functionality)"
    
    return {
        "name": "Test script contains Playwright automation",
        "passed": passed,
        "detail": detail
    }

def check_screenshot_exists(workspace_dir):
    """Check if a screenshot was generated"""
    # Look for common screenshot patterns
    screenshot_patterns = ['*.png', '*.jpg', '*.jpeg']
    screenshots_found = []
    
    for pattern in screenshot_patterns:
        screenshots_found.extend(Path(workspace_dir).glob(f"**/{pattern}"))
    
    # Also check common locations
    common_locations = [
        os.path.join(workspace_dir, 'screenshot.png'),
        os.path.join(workspace_dir, 'final_state.png'),
        os.path.join(workspace_dir, 'todo_app.png'),
        '/tmp/inspect.png',
        '/tmp/screenshot.png'
    ]
    
    for loc in common_locations:
        if os.path.exists(loc):
            screenshots_found.append(Path(loc))
    
    passed = len(screenshots_found) > 0
    
    return {
        "name": "Screenshot generated",
        "passed": passed,
        "detail": f"Found {len(screenshots_found)} screenshot(s): {[str(s) for s in screenshots_found]}"
    }

def check_server_helper_usage(workspace_dir):
    """Check if the with_server.py helper was used or mentioned"""
    # Look for Python files that might contain the automation
    python_files = list(Path(workspace_dir).glob("**/*.py"))
    
    server_helper_used = False
    automation_files = []
    
    for py_file in python_files:
        if py_file.name in ['gen_inputs_script.py', 'eval_script.py']:
            continue
            
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                
            # Check if it's an automation file (contains playwright)
            if 'playwright' in content.lower():
                automation_files.append(str(py_file))
                
                # Check if it properly doesn't start servers (good practice)
                if 'subprocess' not in content and 'npm run' not in content and 'server' not in content.lower():
                    server_helper_used = True
                    
        except Exception:
            continue
    
    passed = server_helper_used or len(automation_files) == 0
    detail = f"Found {len(automation_files)} automation files. Server helper usage: {'Yes' if server_helper_used else 'Not clearly used'}"
    
    return {
        "name": "Proper server management approach",
        "passed": passed,
        "detail": detail
    }

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Usage", "passed": False, "detail": "eval_script.py <workspace_dir>"}]}))
        return
    
    workspace_dir = sys.argv[1]
    checks = []
    
    # Check if React app files exist
    checks.append(check_file_exists(os.path.join(workspace_dir, 'src/App.js'), 'React App.js'))
    checks.append(check_file_exists(os.path.join(workspace_dir, 'package.json'), 'package.json'))
    
    # Look for test/automation scripts
    potential_test_files = [
        'test_todo.py', 'automation.py', 'todo_test.py', 'test.py', 
        'playwright_test.py', 'webapp_test.py'
    ]
    
    test_file_found = None
    for test_file in potential_test_files:
        if os.path.exists(os.path.join(workspace_dir, test_file)):
            test_file_found = os.path.join(workspace_dir, test_file)
            break
    
    # Also look in subdirectories
    if not test_file_found:
        for py_file in Path(workspace_dir).glob("**/*.py"):
            if py_file.name not in ['gen_inputs_script.py', 'eval_script.py']:
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                    if 'playwright' in content.lower():
                        test_file_found = str(py_file)
                        break
                except Exception:
                    continue
    
    if test_file_found:
        checks.append(check_test_script_content(test_file_found))
    else:
        checks.append({
            "name": "Test script exists",
            "passed": False,
            "detail": "No Playwright test script found"
        })
    
    # Check other requirements
    checks.append(check_screenshot_exists(workspace_dir))
    checks.append(check_server_helper_usage(workspace_dir))
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    result = {
        "passed": score >= 0.75,  # Need at least 75% of checks to pass
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()