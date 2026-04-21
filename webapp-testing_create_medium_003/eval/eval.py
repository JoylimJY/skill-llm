import os
import sys
import json
import re
from pathlib import Path

def check_png_valid(path):
    """Check if file is a valid PNG by verifying its magic bytes."""
    try:
        with open(path, 'rb') as f:
            header = f.read(8)
        # PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
        png_signature = b'\x89PNG\r\n\x1a\n'
        if header == png_signature:
            return True, 'Valid PNG image'
        return False, f'Invalid PNG signature'
    except Exception as e:
        return False, f'Error checking PNG: {e}'

def parse_playwright_script(script_path):
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except Exception as e:
        return False, str(e)
    # Check for key Playwright requirements
    checks = {
        'launch_headless': any(k in content for k in ['p.chromium.launch(headless=true)', 'p.chromium.launch(headless = True)']),
        'goto_frontend': 'page.goto(' in content and ('localhost:5173' in content),
        'wait_networkidle': 'page.wait_for_load_state' in content,
        'screenshot': 'page.screenshot' in content,
        'click_load_items': any(k in content for k in ['page.click', 'locator("text=load items"', 'page.locator(', 'click(']),
        'wait_items_list': any(k in content for k in ['page.wait_for_selector', '#items-list']),
        'count_list_items': ('li' in content and '#items-list' in content) or ('locator' in content and 'li' in content),
        'print_items': any(k in content for k in ['print(', 'console.log(', 'print'])
    }
    missing = [k for k,v in checks.items() if not v]
    passed = len(missing) == 0
    detail = f'Playwright script checks passed: {passed}. Missing checks: ' + ', '.join(missing) if missing else 'All key Playwright checks found.'
    return passed, detail

def extract_printed_items(script_path):
    # Try to read lines that print list items
    # We do not run the script, so rely on heuristics that user printed something containing 'Item 1' ... 'Item 5'
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return []
    # Find all print(...) lines
    printed_texts = re.findall(r'print\(([^)]*)\)', content, flags=re.IGNORECASE)
    # Flatten and check for item strings
    texts = []
    for t in printed_texts:
        # Strip quotes
        tclean = t.strip('"\'').strip()
        if tclean:
            texts.append(tclean.lower())
    # Heuristic: The task wants exactly texts for 5 items with "item 1" to "item 5"
    found_items = [s for s in texts if any(f'item {i}' in s for i in range(1,6))]
    return found_items

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg","passed": False, "detail": "Workspace path arg missing"}]}))
        return

    ws = Path(sys.argv[1])

    checks = []

    # Check presence of file homepage.png
    png_path = None
    for f in ws.iterdir():
        if f.name.lower() == 'homepage.png':
            png_path = f
            break
    if png_path is None:
        checks.append({"name": "homepage.png presence", "passed": False, "detail": "homepage.png not found in workspace"})
    else:
        valid, detail = check_png_valid(png_path)
        checks.append({"name": "homepage.png valid PNG", "passed": valid, "detail": detail})

    # Check Playwright script existence and content
    script_path = None
    for f in ws.iterdir():
        if f.name.lower() == 'test_webapp.py':
            script_path = f
            break
    if script_path is None:
        checks.append({"name": "Playwright script presence", "passed": False, "detail": "test_webapp.py not found in workspace"})
    else:
        passed, detail = parse_playwright_script(script_path)
        checks.append({"name": "Playwright script content", "passed": passed, "detail": detail})

        # Check if printed items are present in prints
        printed_items = extract_printed_items(script_path)
        # We expect 5 items containing: item 1 .. item 5
        items_found = set()
        for item in printed_items:
            for i in range(1,6):
                if f'item {i}' in item:
                    items_found.add(i)
        passed_print = (len(items_found) == 5)
        detail_print = f'Printed item texts count: {len(items_found)} expected 5'
        checks.append({"name": "Printed items found", "passed": passed_print, "detail": detail_print})

    score = sum(1 for c in checks if c.get('passed')) / len(checks) if checks else 0.0
    passed = score == 1.0

    print(json.dumps({"passed": passed, "score": score, "checks": checks}))

if __name__ == '__main__':
    main()
