import sys
import os
import json
import re
from pathlib import Path

def score_script(path):
    """Check the Playwright script is valid and performs required actions."""
    script_path = None
    for file in os.listdir(path):
        if file.lower() == 'test_button_click.py':
            script_path = os.path.join(path, file)
            break

    if not script_path:
        return {'name': 'Playwright Script Checks', 'passed': False, 'detail': 'test_button_click.py not found'}

    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except Exception as e:
        return {'name': 'Playwright Script Checks', 'passed': False, 'detail': f'Read error: {e}'}

    passed = True
    detail_msgs = []

    # 1. Check Import (Support both sync and async for robustness)
    if 'playwright' not in content:
        passed = False
        detail_msgs.append("Missing playwright import")

    # 2. Browser Launch (Remove headless=True requirement as it's default)
    if 'chromium.launch' not in content:
        passed = False
        detail_msgs.append("Script must launch chromium")

    # 3. Check page.goto via file://
    if not (('page.goto' in content or 'goto' in content) and 'file://' in content and 'page.html' in content):
        passed = False
        detail_msgs.append("page.goto must load 'page.html' via file:// URL")

    # 4. Check Click Action (Support modern locators)
    # Match: click(), get_by_role, get_by_text, locator, or selector-based click
    click_patterns = [
        r'\.click\(',
        r'get_by_role\s*\(\s*["\']button["\']',
        r'get_by_text\s*\(\s*["\']click me["\']',
        r'["\']#mybtn["\']'
    ]
    if not any(re.search(p, content) for p in click_patterns):
        passed = False
        detail_msgs.append("Script must click the button")

    # 5. Check Verification (Support expect() or manual assertions)
    # Match: expect(...).to_have_text, inner_text, text_content, or simple assert + clicked!
    verify_patterns = [
        r'expect\(',
        r'to_have_text',
        r'inner_text',
        r'text_content',
        r'assert.*clicked!'
    ]
    if not any(re.search(p, content) for p in verify_patterns) or 'clicked!' not in content:
        passed = False
        detail_msgs.append("Script must verify that button's text changes to 'Clicked!'")

    # 6. Check Close
    if 'close()' not in content:
        passed = False
        detail_msgs.append("Script must close the browser/context")

    return {
        'name': 'Playwright Script Checks', 
        'passed': passed, 
        'detail': '; '.join(detail_msgs) if detail_msgs else "All checks passed"
    }

def score_html_file(path):
    """Check the page.html file content (Keep original logic as it passed)."""
    file_path = os.path.join(path, 'page.html')
    if not os.path.exists(file_path):
        return {'name': 'HTML Content Checks', 'passed': False, 'detail': 'page.html missing'}
    
    content = open(file_path, 'r').read().lower()
    passed = True
    details = []
    if '<button' not in content: passed = False; details.append('No <button>')
    if 'id="mybtn"' not in content and "id='mybtn'" not in content: passed = False; details.append('Missing id="mybtn"')
    if 'click me' not in content: passed = False; details.append('Missing initial text')
    if 'clicked!' not in content: passed = False; details.append('Missing "Clicked!" in JS logic')
    
    return {'name': 'HTML Content Checks', 'passed': passed, 'detail': '; '.join(details)}

def main():
    if len(sys.argv) < 2:
        workspace = '.'
    else:
        workspace = sys.argv[1]

    checks = [score_script(workspace), score_html_file(workspace)]
    score = sum(1 for c in checks if c['passed']) / len(checks)
    
    print(json.dumps({
        'passed': score == 1.0,
        'score': score,
        'checks': checks
    }))

if __name__ == '__main__':
    # Verify: python3 -m py_compile eval.py
    main()