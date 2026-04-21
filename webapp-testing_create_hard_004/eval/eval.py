import sys
import os
import json
import subprocess
import time
import glob
from pathlib import Path

def check_file_contains_case_ins(text, keywords):
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False

def find_file_contains_text(dir_path, exts, keywords):
    files = []
    for ext in exts:
        files.extend(Path(dir_path).rglob(f'*{ext}'))
    max_score = 0
    for file in files:
        try:
            content = file.read_text(errors='ignore')
        except:
            continue
        if check_file_contains_case_ins(content, keywords):
            return True
    return False

def run_playwright_script(workspace):
    # Run the frontend_test.py using python in workspace
    try:
        proc = subprocess.run(
            ["python", "frontend_test.py"],
            cwd=workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )
        return proc.returncode == 0, proc.stdout.decode() + proc.stderr.decode()
    except Exception as e:
        return False, str(e)

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0,"checks": [{"name": "args", "passed": False, "detail": "Expected workspace directory path arg."}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    checks = []

    ## Check backend/server.py exists and contains marker
    backend_server = os.path.join(workspace, 'backend', 'server.py')
    if os.path.isfile(backend_server):
        content = ''
        try:
            content = open(backend_server).read()
        except Exception as e:
            pass
        has_marker_backend = 'marker-backend' in content.lower()
        checks.append({
            'name': 'backend server.py presence and marker',
            'passed': has_marker_backend,
            'detail': 'Found backend/server.py with marker string' if has_marker_backend else 'Marker string missing in backend/server.py'
        })
    else:
        checks.append({'name': 'backend server.py presence and marker', 'passed': False, 'detail': 'backend/server.py missing'})

    ## Check frontend/App.js exists and contains marker
    frontend_app = os.path.join(workspace, 'frontend', 'src', 'App.js')
    if os.path.isfile(frontend_app):
        content = ''
        try:
            content = open(frontend_app).read()
        except Exception as e:
            pass
        has_marker_frontend = 'marker-frontend' in content.lower()
        checks.append({
            'name': 'frontend App.js presence and marker',
            'passed': has_marker_frontend,
            'detail': 'Found frontend/src/App.js with marker string' if has_marker_frontend else 'Marker string missing in frontend/src/App.js'
        })
    else:
        checks.append({'name': 'frontend App.js presence and marker', 'passed': False, 'detail': 'frontend/src/App.js missing'})

    ## Check scripts/with_server.py exists
    with_server_py = os.path.join(workspace, 'scripts', 'with_server.py')
    if os.path.isfile(with_server_py):
        checks.append({'name': 'with_server.py presence', 'passed': True, 'detail': 'Found scripts/with_server.py'})
    else:
        checks.append({'name': 'with_server.py presence', 'passed': False, 'detail': 'scripts/with_server.py missing'})

    ## Check frontend_test.py presence
    test_script = os.path.join(workspace, 'frontend_test.py')
    if os.path.isfile(test_script):
        checks.append({'name': 'frontend_test.py presence', 'passed': True, 'detail': 'frontend_test.py exists'})
    else:
        checks.append({'name': 'frontend_test.py presence', 'passed': False, 'detail': 'frontend_test.py missing'})

    ## If test script missing, no point proceeding to run
    if not os.path.isfile(test_script):
        passed = all(c['passed'] for c in checks)
        score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
        print(json.dumps({"passed": passed, "score": score, "checks": checks}))
        sys.exit(0)

    ## Run the automated test script using scripts/with_server.py to launch servers and then frontend_test.py
    # Compose command:
    # python scripts/with_server.py \
    #  --server "cd backend && python server.py" --port 3000 \
    #  --server "cd frontend && npm run dev" --port 5173 \
    #  -- python frontend_test.py

    with_server_py_abs = os.path.join(workspace, 'scripts', 'with_server.py')

    cmd = ["python", with_server_py_abs,
           "--server", "cd backend && python server.py", "--port", "3000",
           "--server", "cd frontend && npm run dev", "--port", "5173",
           "--", "python", "frontend_test.py"]

    try:
        proc = subprocess.run(cmd, cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        retcode_ok = proc.returncode == 0
        output_log = proc.stdout.decode() + proc.stderr.decode()
    except Exception as e:
        retcode_ok = False
        output_log = str(e)

    checks.append({'name': 'run automated test script with with_server.py', 'passed': retcode_ok,
                   'detail': 'Process returned 0' if retcode_ok else f'Failed, output: {output_log[:300]}...'})

    ## Check screenshot file
    screenshot_path = os.path.join(workspace, 'frontend_screenshot.png')
    screenshot_exists = os.path.isfile(screenshot_path) and os.path.getsize(screenshot_path) > 1000
    checks.append({'name': 'screenshot exists and nonempty', 'passed': screenshot_exists,
                   'detail': 'frontend_screenshot.png found and >1KB' if screenshot_exists else 'Missing or too small screenshot'})

    ## Check console log file
    console_log_path = os.path.join(workspace, 'frontend_console.log')
    console_exists = os.path.isfile(console_log_path) and os.path.getsize(console_log_path) > 0
    console_valid = False
    if console_exists:
        try:
            cl_text = open(console_log_path, 'r', encoding='utf-8', errors='ignore').read()
            # Check console log contains some expected JS console log text like 'Fetch Message' or 'Refetch'
            console_valid = check_file_contains_case_ins(cl_text, ['fetch message', 'refetch', 'error', 'warning'])
        except:
            console_valid = False
    checks.append({'name': 'console log exists and contains expected logs', 'passed': console_exists and console_valid,
                   'detail': 'frontend_console.log has expected console messages' if console_exists and console_valid else 'Missing or console log does not contain expected keywords'})

    ## Check that the rendered page after click contains the backend message and button text changed
    # Because we only have screenshot and console logs from the script, parse screenshot is complex,
    # Instead rely on console log and that test script ran successfully.

    ## Check frontend_test.py source for required logic (click button, check messages)
    try:
        test_code = open(test_script).read().lower()
        has_fetch_click = 'click' in test_code and 'fetch message' in test_code
        has_wait_for_networkidle = "page.wait_for_load_state('networkidle')" in test_code
        has_screenshot = 'screenshot' in test_code
        has_console_log_capture = 'console' in test_code and '.log' in test_code
        has_check_refetch = 'refetch' in test_code
    except Exception as e:
        has_fetch_click = has_wait_for_networkidle = has_screenshot = has_console_log_capture = has_check_refetch = False

    checks.append({'name': 'frontend_test.py contains click on Fetch Message button',
                   'passed': has_fetch_click,
                   'detail': 'Found click + Fetch Message logic' if has_fetch_click else 'Missing click on Fetch Message button'})
    checks.append({'name': 'frontend_test.py waits for networkidle state',
                   'passed': has_wait_for_networkidle,
                   'detail': 'Waits for networkidle' if has_wait_for_networkidle else 'Missing wait_for_load_state networkidle'})
    checks.append({'name': 'frontend_test.py captures and saves console logs',
                   'passed': has_console_log_capture,
                   'detail': 'Console log capture present' if has_console_log_capture else 'No console log capture'})
    checks.append({'name': 'frontend_test.py takes full page screenshot',
                   'passed': has_screenshot,
                   'detail': 'Takes screenshot' if has_screenshot else 'No screenshot code'})
    checks.append({'name': 'frontend_test.py verifies button text changes to Refetch',
                   'passed': has_check_refetch,
                   'detail': 'Checks button text changed to Refetch' if has_check_refetch else 'No check for Refetch button text'})

    # Calculate score
    passed_count = sum(1 for c in checks if c['passed'])
    total_count = len(checks) if checks else 1
    score = passed_count / total_count
    passed = score == 1.0

    print(json.dumps({"passed": passed, "score": score, "checks": checks}))

if __name__ == '__main__':
    main()
