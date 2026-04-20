import json
from pathlib import Path

checks = []
workspace = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
if len(__import__('sys').argv) > 1:
    workspace = Path(__import__('sys').argv[1])

passed_count = 0

def add_check(name, passed, detail):
    global passed_count
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
    if passed:
        passed_count += 1

# Check 1: output exists
try:
    output_path = workspace / 'output.txt'
    exists = output_path.exists()
    add_check('output_exists', exists, 'output.txt found' if exists else 'output.txt is missing')
except Exception as e:
    add_check('output_exists', False, f'error checking output.txt: {e}')

# Check 2: marker-aware content check
try:
    text = ''
    if (workspace / 'output.txt').exists():
        text = (workspace / 'output.txt').read_text(encoding='utf-8', errors='replace')
    normalized = ' '.join(text.lower().split())
    contains_groq = 'groq' in normalized
    under_limit = len(text.split()) <= 120 if text else False
    add_check('content_mentions_groq_and_word_limit', contains_groq and under_limit, f'contains_groq={contains_groq}, word_count={len(text.split()) if text else 0}')
except Exception as e:
    add_check('content_mentions_groq_and_word_limit', False, f'error reading output.txt: {e}')

# Check 3: no obvious placeholder text
try:
    text = ''
    if (workspace / 'output.txt').exists():
        text = (workspace / 'output.txt').read_text(encoding='utf-8', errors='replace')
    bad_markers = ['lorem ipsum', 'placeholder', 'todo']
    lowered = text.lower()
    clean = not any(m in lowered for m in bad_markers)
    add_check('no_placeholder_text', clean, 'no obvious placeholder language found' if clean else 'placeholder-like text detected')
except Exception as e:
    add_check('no_placeholder_text', False, f'error validating content: {e}')

score = (passed_count / len(checks)) if checks else 0.0
result = {"passed": passed_count == len(checks) and len(checks) > 0, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
