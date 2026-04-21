import json
import os
import sys
import re


def check_file_contains_text(filepath, text_list):
    """Check if file contains all texts (case insensitive)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            for text in text_list:
                if text.lower() not in content:
                    return False
            return True
    except Exception:
        return False


def evaluate(workspace):
    checks = []

    # Check test_playwright.py exists and has expected indications
    script_path = None
    for root, dirs, files in os.walk(workspace):
        for file in files:
            if file == 'test_playwright.py':
                script_path = os.path.join(root, file)
                break
        if script_path:
            break
    if script_path is None:
        checks.append({"name": "Playwright script file exists", "passed": False, "detail": "Missing test_playwright.py"})
    else:
        # Check script contains key commands
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                code = f.read().lower()
            button_click_check = 'load data' in code and 'page.locator' in code and 'click' in code
            screenshot_check = 'screenshot' in code
            console_log_check = 'console' in code

            checks.append({"name": "Playwright script contains button click code", "passed": button_click_check, "detail": "Contains locator and click of 'Load Data' button"})
            checks.append({"name": "Playwright script takes screenshot", "passed": screenshot_check, "detail": "Code takes page screenshot"})
            checks.append({"name": "Playwright script captures console logs", "passed": console_log_check, "detail": "Code captures or subscribes to console events"})
        except Exception as e:
            checks.append({"name": "Playwright script file readable", "passed": False, "detail": f"Error reading script: {e}"})

    # Check screenshot file
    screenshot_path = os.path.join(workspace, 'screenshot_inspect.png')
    if os.path.isfile(screenshot_path):
        # Basic check: file exists and is non-empty
        size = os.path.getsize(screenshot_path)
        passed = size > 0
        detail = f"Screenshot size: {size} bytes"
    else:
        passed = False
        detail = "screenshot_inspect.png not found"
    checks.append({"name": "Screenshot file exists and valid", "passed": passed, "detail": detail})

    # Check console_logs.txt file
    console_log_path = os.path.join(workspace, 'console_logs.txt')
    if os.path.isfile(console_log_path):
        try:
            with open(console_log_path, 'r', encoding='utf-8') as f:
                lines = f.read().lower()
            # Check some common log words present
            passed = ('log' in lines or 'console' in lines) and len(lines) > 0
            detail = f"Console log file length: {len(lines)} characters"
        except Exception as e:
            passed = False
            detail = f"Error reading console_logs.txt: {e}"
    else:
        passed = False
        detail = "console_logs.txt not found"
    checks.append({"name": "Console logs file exists", "passed": passed, "detail": detail})

    # Check script output for discovered buttons text
    # We look for printed list of buttons containing 'Load Data'
    discovered_buttons_found = False
    interaction_success = False
    try:
        # Search all .log or .txt or .out files for output
        for root, dirs, files in os.walk(workspace):
            for file in files:
                if file.endswith(('.log', '.txt', '.out', '.stdout', '.stderr')) or file == 'test_playwright.py':
                    continue
                fullp = os.path.join(root, file)
                try:
                    with open(fullp, 'r', encoding='utf-8') as f:
                        text = f.read().lower()
                        if 'buttons found' in text and 'load data' in text:
                            discovered_buttons_found = True
                        if 'item-1 found in list' in text:
                            interaction_success = True
                except Exception:
                    pass
    except Exception:
        pass

    # As fallback check stdout live
    # Actually to cover partial might search output elsewhere

    checks.append({"name": "Reconnaissance printed buttons including 'Load Data'", "passed": discovered_buttons_found, "detail": "Detected output listing buttons including 'Load Data'"})
    checks.append({"name": "Interaction verifies 'Item-1' presence", "passed": interaction_success, "detail": "Detected output confirming 'Item-1' in loaded list"})

    # Score & pass decision
    score = sum(check['passed'] for check in checks) / max(1, len(checks))
    passed = score == 1.0

    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argparse", "passed": False, "detail": "Workspace path argument required"}]}))
        sys.exit(1)
    evaluate(sys.argv[1])
