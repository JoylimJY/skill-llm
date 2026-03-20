#!/usr/bin/env python3
import sys
import os
import json
import glob
from pathlib import Path

def main(workspace_dir):
    checks = []
    score = 0.0
    
    # Check if automation script exists
    py_files = list(Path(workspace_dir).glob('*.py'))
    automation_files = [f for f in py_files if 'automation' in f.name.lower() or 'test' in f.name.lower()]
    
    if not automation_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "automation_script_exists", "passed": False, "detail": "No automation script found"}]
        }
    
    checks.append({"name": "automation_script_exists", "passed": True, "detail": f"Found: {automation_files[0].name}"})
    score += 0.1
    
    # Check script uses Playwright
    script_content = automation_files[0].read_text()
    uses_playwright = 'playwright' in script_content.lower()
    checks.append({"name": "uses_playwright", "passed": uses_playwright, "detail": "Script imports Playwright" if uses_playwright else "No Playwright import found"})
    if uses_playwright:
        score += 0.1
    
    # Check script uses with_server.py or manages servers
    uses_server_helper = 'with_server.py' in script_content or ('subprocess' in script_content and 'port' in script_content)
    checks.append({"name": "manages_servers", "passed": uses_server_helper, "detail": "Uses server management" if uses_server_helper else "No server management found"})
    if uses_server_helper:
        score += 0.15
    
    # Check for key automation elements
    automation_elements = {
        'navigates_to_page': any(x in script_content for x in ['goto', 'localhost:3000']),
        'waits_for_load': 'networkidle' in script_content or 'wait_for_' in script_content,
        'clicks_add_button': any(x in script_content for x in ['click', 'add', 'button']),
        'fills_form': any(x in script_content for x in ['fill', 'type', 'input']),
        'submits_form': any(x in script_content for x in ['submit', 'click']),
        'takes_screenshot': 'screenshot' in script_content,
        'captures_console': 'console' in script_content or 'on(' in script_content
    }
    
    for element, present in automation_elements.items():
        checks.append({"name": element, "passed": present, "detail": f"Found {element.replace('_', ' ')}" if present else f"Missing {element.replace('_', ' ')}"})
        if present:
            score += 0.1
    
    # Check for specific test data (John Doe, john@example.com)
    has_test_data = 'john' in script_content.lower() and 'doe' in script_content.lower()
    checks.append({"name": "uses_specified_test_data", "passed": has_test_data, "detail": "Uses John Doe test data" if has_test_data else "Missing specified test data"})
    if has_test_data:
        score += 0.1
    
    # Check for verification steps
    has_verification = any(x in script_content.lower() for x in ['assert', 'verify', 'check', 'wait_for_selector'])
    checks.append({"name": "includes_verification", "passed": has_verification, "detail": "Includes verification steps" if has_verification else "No verification found"})
    if has_verification:
        score += 0.1
    
    # Check if screenshot file exists (if script was run)
    screenshot_files = list(Path(workspace_dir).glob('*.png')) + list(Path(workspace_dir).glob('**/*.png'))
    has_screenshot_output = len(screenshot_files) > 0
    checks.append({"name": "screenshot_generated", "passed": has_screenshot_output, "detail": f"Screenshot found: {screenshot_files[0].name}" if has_screenshot_output else "No screenshot file found"})
    if has_screenshot_output:
        score += 0.05
    
    # Bonus points for robust patterns
    robust_patterns = {
        'error_handling': any(x in script_content for x in ['try:', 'except:', 'catch']),
        'multiple_servers': script_content.count('--server') > 1 or script_content.count('port') > 2,
        'proper_waits': 'wait_for_selector' in script_content or 'wait_for_timeout' in script_content
    }
    
    for pattern, present in robust_patterns.items():
        if present:
            score += 0.05
    
    # Overall pass/fail
    passed = score >= 0.6
    
    return {
        "passed": passed,
        "score": min(1.0, score),
        "checks": checks
    }

if __name__ == '__main__':
    result = main(sys.argv[1])
    print(json.dumps(result, indent=2))