import sys
import os
import json
import glob

workspace = sys.argv[1]

checks = []

# Check 1: test_results.json exists
results_candidates = glob.glob(os.path.join(workspace, 'test_results.json'))
results_file = None
if results_candidates:
    results_file = results_candidates[0]

checks.append({
    'name': 'test_results.json exists',
    'passed': results_file is not None,
    'detail': f'Found at {results_file}' if results_file else 'test_results.json not found in workspace'
})

results_data = {}
if results_file:
    try:
        with open(results_file, 'r') as f:
            results_data = json.load(f)
    except Exception as e:
        checks.append({
            'name': 'test_results.json is valid JSON',
            'passed': False,
            'detail': f'Failed to parse JSON: {e}'
        })
        results_data = {}
    else:
        checks.append({
            'name': 'test_results.json is valid JSON',
            'passed': True,
            'detail': 'Successfully parsed'
        })
else:
    checks.append({
        'name': 'test_results.json is valid JSON',
        'passed': False,
        'detail': 'File not found, cannot parse'
    })

# Check 3: total_items == 3
total_items = results_data.get('total_items', None)
checks.append({
    'name': 'total_items equals 3',
    'passed': total_items == 3,
    'detail': f'total_items={total_items}'
})

# Check 4: completed_items contains 'Walk the dog'
completed_items = results_data.get('completed_items', [])
if not isinstance(completed_items, list):
    completed_items = []
completed_lower = [str(x).lower() for x in completed_items]
walk_dog_completed = any('walk the dog' in item for item in completed_lower)
checks.append({
    'name': "completed_items contains 'Walk the dog'",
    'passed': walk_dog_completed,
    'detail': f'completed_items={completed_items}'
})

# Check 5: screenshot_path is set and file exists
screenshot_path = results_data.get('screenshot_path', '')
screenshot_exists = False
if screenshot_path:
    screenshot_exists = os.path.isfile(str(screenshot_path))
# Also check /tmp/todo_test.png directly as fallback
if not screenshot_exists:
    screenshot_exists = os.path.isfile('/tmp/todo_test.png')
checks.append({
    'name': 'Screenshot file exists',
    'passed': screenshot_exists,
    'detail': f'screenshot_path={screenshot_path}, /tmp/todo_test.png exists={os.path.isfile("/tmp/todo_test.png")}'
})

# Check 6: all_checks_passed is True
all_checks_passed = results_data.get('all_checks_passed', None)
checks.append({
    'name': 'all_checks_passed is True',
    'passed': all_checks_passed is True,
    'detail': f'all_checks_passed={all_checks_passed}'
})

# Check 7: completed_items does NOT contain 'Buy groceries' or 'Read a book'
unexpected_completed = [item for item in completed_lower if 'buy groceries' in item or 'read a book' in item]
checks.append({
    'name': "Only 'Walk the dog' is completed (not others)",
    'passed': len(unexpected_completed) == 0,
    'detail': f'Unexpected completed items: {unexpected_completed}'
})

# Check 8: screenshot_path key exists in JSON
checks.append({
    'name': 'screenshot_path key present in JSON',
    'passed': 'screenshot_path' in results_data,
    'detail': f'Keys found: {list(results_data.keys())}'
})

total = len(checks)
passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / total
overall_passed = score >= 0.8

result = {
    'passed': overall_passed,
    'score': score,
    'checks': checks
}

print(json.dumps(result, indent=2))
