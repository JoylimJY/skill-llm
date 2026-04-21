import sys
import os
import json
import re

def find_script_file(workspace):
    candidates = []
    for root, _, files in os.walk(workspace):
        for filename in files:
            if filename.lower() == 'test_button_click.py':
                candidates.append(os.path.join(root, filename))
    return candidates[0] if candidates else None

def check_script_content(path):
    # Check that the script imports sync_playwright
    # Waits for networkidle, finds button with text 'Click Me', clicks, waits for #result, prints text, takes screenshot, closes browser
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().lower()

    checks = []
    checks.append(('imports_playwright', 'from playwright.sync_api import sync_playwright' in content))
    checks.append(('launches_chromium', 'chromium.launch(' in content))
    checks.append(('headless_true', re.search(r'headless\s*=\s*true', content) is not None))
    checks.append(('goto_localhost', 'page.goto(' in content and ('localhost:5173' in content or 'localhost:5173' in content)) )
    checks.append(('wait_networkidle', 'wait_for_load_state(' in content and 'networkidle' in content))
    # Check that it takes a screenshot and saves as page.png
    checks.append(('takes_screenshot', ('page.screenshot(' in content and 'page.png' in content)))
    # Check for locating button with text 'Click Me'
    checks.append(('finds_button_text', 'click me' in content))
    # Check that the script clicks the button
    checks.append(('clicks_button', '.click()' in content))
    # Check waits for '#result' element
    checks.append(('waits_for_result', ('wait_for_selector' in content and '#result' in content)))
    # Check prints the text content of #result
    checks.append(('prints_result_text', 'print(' in content and ('result' in content or 'result.text_content' in content)))
    # Check that browser closes (browser.close())
    checks.append(('closes_browser', 'browser.close()' in content))

    passed_checks = [c for c in checks if c[1]]

    score = len(passed_checks) / len(checks)
    passed = score == 1.0

    detail = ', '.join([name for name, passed_flag in checks if passed_flag])

    return passed, score, checks, detail

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Expected workspace directory argument"}]}))
        sys.exit(1)

    workspace = sys.argv[1]

    results = []
    total_checks = []

    # Find the script file
    script_path = find_script_file(workspace)

    if script_path is None:
        result = {"passed": False, "score": 0.0, "checks": [{"name": "script_found", "passed": False, "detail": "test_button_click.py not found"}]}
        print(json.dumps(result))
        sys.exit(0)

    passed, score, checks, detail = check_script_content(script_path)

    checks_out = []
    for name, passed_flag in checks:
        checks_out.append({"name": name, "passed": passed_flag, "detail": ""})

    result = {
        "passed": passed,
        "score": score,
        "checks": checks_out
    }

    print(json.dumps(result))
