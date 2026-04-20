import json
import os
import re
from pathlib import Path


def normalize(text):
    try:
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^a-z0-9_\-/.: ]+', '', text)
        return text.strip()
    except Exception:
        return ''


def load_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


workspace = Path(os.sys.argv[1])
checks = []
passed_count = 0

def add_check(name, passed, detail):
    global passed_count
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})
    if passed:
        passed_count += 1

# Check 1: output exists
try:
    out_path = workspace / 'output.txt'
    exists = out_path.exists()
    add_check('output_exists', exists, 'output.txt found' if exists else 'output.txt is missing')
except Exception as e:
    add_check('output_exists', False, f'exception while checking file existence: {e}')

# Check 2: contains top 3 model names or fuzzy equivalents
try:
    text = (workspace / 'output.txt').read_text(encoding='utf-8', errors='replace') if (workspace / 'output.txt').exists() else ''
    nt = normalize(text)
    targets = [
        'qwen/qwen2.5-coder-7b-instruct',
        'deepseek-ai/deepseek-coder-v2-lite-instruct',
        'mistralai/mistral-7b-instruct-v0.3',
    ]
    found = sum(1 for t in targets if normalize(t) in nt)
    add_check('contains_three_models', found >= 3, f'found {found}/3 expected model names')
except Exception as e:
    add_check('contains_three_models', False, f'exception while scanning output text: {e}')

# Check 3: mentions fit levels and quantization/speed language
try:
    text = (workspace / 'output.txt').read_text(encoding='utf-8', errors='replace') if (workspace / 'output.txt').exists() else ''
    nt = normalize(text)
    required_terms = ['perfect', 'good', 'q5_k_m', 'q4_k_m', 'tps']
    found_terms = [term for term in required_terms if term in nt]
    add_check('mentions_fit_and_speed', len(found_terms) >= 4, f'found terms: {found_terms}')
except Exception as e:
    add_check('mentions_fit_and_speed', False, f'exception while validating content: {e}')

# Check 4: terminal-friendly format with at least 3 non-empty lines
try:
    text = (workspace / 'output.txt').read_text(encoding='utf-8', errors='replace') if (workspace / 'output.txt').exists() else ''
    lines = [ln for ln in text.splitlines() if ln.strip()]
    add_check('has_multiple_lines', len(lines) >= 3, f'non-empty line count: {len(lines)}')
except Exception as e:
    add_check('has_multiple_lines', False, f'exception while counting lines: {e}')

result = {
    'passed': passed_count == len(checks) and len(checks) > 0,
    'score': (passed_count / len(checks)) if checks else 0.0,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False))
