import os
import sys
import json
import re

workspace = sys.argv[1]

result = {"passed": False, "score": 0.0, "checks": []}

# Helper function to find files containing or matching patterns

def find_files_with_ext(ext):
    files = []
    for dirpath, _, filenames in os.walk(workspace):
        for f in filenames:
            if f.lower().endswith(ext.lower()):
                files.append(os.path.join(dirpath, f))
    return files

# Check 1: Check that 'automation.py' exists
automation_py = None
for dirpath, _, files in os.walk(workspace):
    for f in files:
        if f.lower() == 'automation.py':
            automation_py = os.path.join(dirpath, f)
            break
    if automation_py:
        break

check1_passed = automation_py is not None
result["checks"].append({"name": "automation.py script file existence", "passed": check1_passed, "detail": "Found automation.py script." if check1_passed else "automation.py is missing."})

# Check 2: Verify automation.py is a valid Python file and contains expected Playwright usage
check2_passed = False
if check1_passed:
    try:
        with open(automation_py, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        # Must import playwright sync
        cond1 = 'from playwright.sync_api' in content
        cond2 = 'page.goto(' in content
        cond3 = '.wait_for_load_state(' in content
        cond4 = 'browser.close(' in content
        cond5 = 'button' in content # presence of button locator invocation is reasonable
        # Also at least one click statement
        cond6 = '.click(' in content
        check2_passed = cond1 and cond2 and cond3 and cond4 and cond5 and cond6
    except Exception as e:
        check2_passed = False

result["checks"].append({"name": "automation.py uses Playwright correctly", "passed": check2_passed, "detail": "Detected proper Playwright sync usage, navigation, waits, click, and browser close." if check2_passed else "Playwright usage or navigation/click/wait pattern missing."})

# Check 3: Check screenshot file exists and is not empty
screenshot_path = None
for dirpath, _, files in os.walk(workspace):
    for f in files:
        if f.lower() == 'rendered_page.png':
            screenshot_path = os.path.join(dirpath, f)
            break
    if screenshot_path:
        break

check3_passed = False
if screenshot_path:
    try:
        size = os.path.getsize(screenshot_path)
        check3_passed = size > 5000  # Arbitrary small size >5KB to avoid empty
    except:
        check3_passed = False

result["checks"].append({"name": "Rendered page screenshot exists and nontrivial size", "passed": check3_passed, "detail": f"Screenshot file found with size {size} bytes." if check3_passed else "Screenshot missing or too small."})

# Check 4: Check that automation.py prints the expected new list item text matching the marker
# Marker text: 'MarkerItem-12345'
# We'll accept it printed to stdout anywhere

print_found = False
try:
    output_file = os.path.join(workspace, 'automation_stdout.txt')
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            out = f.read().lower()
        mark = 'markeritem-12345'
        if mark in out:
            print_found = True
except Exception:
    print_found = False

# If no explicit stdout capture file, try to find any .txt, .log file containing marker
if not print_found:
    for dirpath, _, files in os.walk(workspace):
        for f in files:
            if f.lower().endswith(('.txt', '.log', '.out')):
                path = os.path.join(dirpath, f)
                try:
                    with open(path, 'r', encoding='utf-8') as ff:
                        content = ff.read().lower()
                    if 'markeritem-12345' in content:
                        print_found = True
                        break
                except Exception:
                    pass
        if print_found:
            break

result["checks"].append({"name": "Output contains printed marker new list item text", "passed": print_found, "detail": "Found printed text for new list item: MarkerItem-12345." if print_found else "Marker text not found in printed output."})

# Check 5: Check that automation.py includes wait for selector after click for new list item
# Look for wait_for_selector or similar for li (list item)
wait_li_found = False
if check1_passed:
    try:
        with open(automation_py, 'r', encoding='utf-8') as f:
            lines = f.read().lower()
        # Simple check for wait_for_selector with li or list item
        if re.search(r'wait_for_selector\(("|\')li("|\')', lines) or 'wait_for_selector' in lines:
            wait_li_found = True
    except Exception:
        wait_li_found = False

result["checks"].append({"name": "Wait for new list item after button click detecte", "passed": wait_li_found, "detail": "Found wait_for_selector for list item after clicking." if wait_li_found else "No wait_for_selector for new list item after click detected."})

# Compute final score
passed_cnt = sum(1 for c in result["checks"] if c["passed"])
total = len(result["checks"])
result["score"] = passed_cnt / total if total > 0 else 0.0
# pass if score == 1.0
result["passed"] = (result["score"] == 1.0)

print(json.dumps(result))
