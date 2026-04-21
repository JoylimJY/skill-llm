import sys
import os
import json
import subprocess
import glob

workspace = sys.argv[1]

checks = []

# Find the test script
script_candidates = glob.glob(os.path.join(workspace, 'test_page.py'))
if not script_candidates:
    script_candidates = glob.glob(os.path.join(workspace, '**', 'test_page.py'), recursive=True)

script_found = len(script_candidates) > 0
checks.append({
    'name': 'test_page.py exists',
    'passed': script_found,
    'detail': f'Found at {script_candidates[0]}' if script_found else 'test_page.py not found in workspace'
})

output_data = None
run_success = False

if script_found:
    script_path = script_candidates[0]
    script_dir = os.path.dirname(script_path)
    try:
        result = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=script_dir
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        run_success = result.returncode == 0

        # Try to parse JSON from stdout
        # Look for a JSON object in the output
        json_start = stdout.find('{')
        json_end = stdout.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            try:
                output_data = json.loads(json_str)
            except json.JSONDecodeError:
                output_data = None

        checks.append({
            'name': 'script runs without error',
            'passed': run_success,
            'detail': f'Return code: {result.returncode}. Stderr: {stderr[:300]}' if not run_success else 'Script ran successfully'
        })
    except subprocess.TimeoutExpired:
        checks.append({
            'name': 'script runs without error',
            'passed': False,
            'detail': 'Script timed out after 60 seconds'
        })
    except Exception as e:
        checks.append({
            'name': 'script runs without error',
            'passed': False,
            'detail': f'Exception: {str(e)}'
        })
else:
    checks.append({
        'name': 'script runs without error',
        'passed': False,
        'detail': 'Cannot run script: file not found'
    })

# Check JSON output structure and values
if output_data is not None:
    title_check = output_data.get('title_check', False)
    checks.append({
        'name': 'title_check is true in output',
        'passed': bool(title_check),
        'detail': f'title_check = {title_check}'
    })

    h1_check = output_data.get('h1_check', False)
    checks.append({
        'name': 'h1_check is true in output',
        'passed': bool(h1_check),
        'detail': f'h1_check = {h1_check}'
    })

    button_exists = output_data.get('button_exists', False)
    checks.append({
        'name': 'button_exists is true in output',
        'passed': bool(button_exists),
        'detail': f'button_exists = {button_exists}'
    })

    click_check = output_data.get('click_check', False)
    checks.append({
        'name': 'click_check is true in output',
        'passed': bool(click_check),
        'detail': f'click_check = {click_check}'
    })
else:
    for check_name in ['title_check is true in output', 'h1_check is true in output', 'button_exists is true in output', 'click_check is true in output']:
        checks.append({
            'name': check_name,
            'passed': False,
            'detail': 'No valid JSON output found from script'
        })

# Check that the script uses file:// URL pattern or reads from app/index.html
if script_found:
    with open(script_candidates[0], 'r') as f:
        script_content = f.read()
    uses_file_url = 'file://' in script_content or 'file:\\\\' in script_content.lower()
    uses_playwright = 'playwright' in script_content.lower()
    checks.append({
        'name': 'script uses Playwright',
        'passed': uses_playwright,
        'detail': 'playwright import found' if uses_playwright else 'No playwright usage found in script'
    })
    checks.append({
        'name': 'script uses file:// URL',
        'passed': uses_file_url,
        'detail': 'file:// URL found in script' if uses_file_url else 'No file:// URL found in script'
    })
else:
    checks.append({'name': 'script uses Playwright', 'passed': False, 'detail': 'Script not found'})
    checks.append({'name': 'script uses file:// URL', 'passed': False, 'detail': 'Script not found'})

total = len(checks)
passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / total if total > 0 else 0.0

result = {
    'passed': score >= 0.8,
    'score': score,
    'checks': checks
}

print(json.dumps(result, indent=2))
