#!/usr/bin/env python3
import sys
import os
import json
import glob
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Expected workspace path argument"}]}))
        return
    
    workspace = sys.argv[1]
    checks = []
    
    # Check if a Python test script was created
    py_files = list(Path(workspace).glob('*.py'))
    test_files = [f for f in py_files if 'test' in f.name.lower() or 'automation' in f.name.lower()]
    
    if not test_files:
        checks.append({"name": "test_script_exists", "passed": False, "detail": "No test/automation Python script found"})
    else:
        checks.append({"name": "test_script_exists", "passed": True, "detail": f"Found test script: {test_files[0].name}"})
        
        # Read the test script content
        script_content = test_files[0].read_text()
        
        # Check for Playwright imports
        has_playwright = 'playwright' in script_content.lower()
        checks.append({"name": "uses_playwright", "passed": has_playwright, "detail": "Script imports Playwright" if has_playwright else "Script should import Playwright"})
        
        # Check for file:// URL usage (since it's a static HTML file)
        has_file_url = 'file://' in script_content
        checks.append({"name": "uses_file_url", "passed": has_file_url, "detail": "Script uses file:// URL for local HTML" if has_file_url else "Script should use file:// URL for static HTML"})
        
        # Check for form interaction elements
        has_username_fill = 'username' in script_content and ('fill' in script_content or 'type' in script_content)
        checks.append({"name": "fills_username", "passed": has_username_fill, "detail": "Script fills username field" if has_username_fill else "Script should fill username field"})
        
        has_password_fill = 'password' in script_content and ('fill' in script_content or 'type' in script_content)
        checks.append({"name": "fills_password", "passed": has_password_fill, "detail": "Script fills password field" if has_password_fill else "Script should fill password field"})
        
        has_submit_click = 'click' in script_content and ('submit' in script_content.lower() or 'button' in script_content.lower())
        checks.append({"name": "clicks_submit", "passed": has_submit_click, "detail": "Script clicks submit button" if has_submit_click else "Script should click submit button"})
        
        # Check for screenshot
        has_screenshot = 'screenshot' in script_content
        checks.append({"name": "takes_screenshot", "passed": has_screenshot, "detail": "Script takes screenshot" if has_screenshot else "Script should take a screenshot"})
    
    # Check if screenshot file was actually created
    screenshot_files = list(Path(workspace).glob('*.png')) + list(Path(workspace).glob('*.jpg')) + list(Path(workspace).glob('*.jpeg'))
    has_screenshot_file = len(screenshot_files) > 0
    checks.append({"name": "screenshot_file_exists", "passed": has_screenshot_file, "detail": f"Screenshot file created: {screenshot_files[0].name}" if has_screenshot_file else "No screenshot file found"})
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    passed = score >= 0.7  # Pass if at least 70% of checks pass
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()