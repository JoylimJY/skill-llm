from pathlib import Path
import json
import re
import sys


def norm(text):
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


checks = []
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

# Check 1: output file exists
try:
    out_path = workspace / 'output.md'
    exists = out_path.exists()
    checks.append({
        'name': 'output_file_exists',
        'passed': exists,
        'detail': 'output.md found' if exists else 'output.md is missing'
    })
except Exception as e:
    checks.append({'name': 'output_file_exists', 'passed': False, 'detail': f'Error checking file existence: {e}'})

# Check 2: contains required phrase
try:
    text, err = safe_read(workspace / 'output.md')
    if text is None:
        checks.append({'name': 'contains_required_phrase', 'passed': False, 'detail': f'Could not read output.md: {err}'})
    else:
        passed = 'deepseek reasoner lite agent' in norm(text)
        checks.append({
            'name': 'contains_required_phrase',
            'passed': passed,
            'detail': 'Required phrase present' if passed else 'Required phrase not found'
        })
except Exception as e:
    checks.append({'name': 'contains_required_phrase', 'passed': False, 'detail': f'Error: {e}'})

# Check 3: has 3 bullet items
try:
    text, err = safe_read(workspace / 'output.md')
    if text is None:
        checks.append({'name': 'has_three_bullets', 'passed': False, 'detail': f'Could not read output.md: {err}'})
    else:
        bullet_lines = [line for line in text.splitlines() if re.match(r'^\s*[-*]\s+\S+', line)]
        passed = len(bullet_lines) >= 3
        checks.append({
            'name': 'has_three_bullets',
            'passed': passed,
            'detail': f'Found {len(bullet_lines)} bullet lines' if bullet_lines else 'No bullet lines found'
        })
except Exception as e:
    checks.append({'name': 'has_three_bullets', 'passed': False, 'detail': f'Error: {e}'})

# Check 4: final line requirement
try:
    text, err = safe_read(workspace / 'output.md')
    if text is None:
        checks.append({'name': 'has_final_line', 'passed': False, 'detail': f'Could not read output.md: {err}'})
    else:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        passed = bool(lines) and 'generated for benchmark evaluation.' in norm(lines[-1])
        checks.append({
            'name': 'has_final_line',
            'passed': passed,
            'detail': 'Final line matches expectation' if passed else (f'Final line was: {lines[-1]}' if lines else 'File is empty')
        })
except Exception as e:
    checks.append({'name': 'has_final_line', 'passed': False, 'detail': f'Error: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
