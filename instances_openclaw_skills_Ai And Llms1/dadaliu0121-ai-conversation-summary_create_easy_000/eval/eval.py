import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore'), None
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        s = s.lower()
        s = re.sub(r'[^a-z0-9]+', ' ', s)
        return re.sub(r'\s+', ' ', s).strip()
    except Exception:
        return ''


workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
checks = []

# Check 1: output file exists
try:
    output_path = workspace / 'output.txt'
    exists = output_path.exists()
    detail = 'output.txt found' if exists else 'output.txt is missing'
    checks.append({'name': 'output_exists', 'passed': bool(exists), 'detail': detail})
except Exception as e:
    checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking output.txt: {e}'})

# Check 2: summary mentions key points
try:
    text, err = safe_read_text(workspace / 'output.txt')
    if text is None:
        checks.append({'name': 'summary_content', 'passed': False, 'detail': f'could not read output.txt: {err}'})
    else:
        n = normalize(text)
        keywords = ['timeline', 'planning', 'implementation', 'review', 'weekly', 'status']
        hits = [k for k in keywords if k in n]
        passed = len(hits) >= 3
        checks.append({'name': 'summary_content', 'passed': passed, 'detail': f'found keywords: {hits}'})
except Exception as e:
    checks.append({'name': 'summary_content', 'passed': False, 'detail': f'error validating content: {e}'})

# Check 3: summary is concise
try:
    text, err = safe_read_text(workspace / 'output.txt')
    if text is None:
        checks.append({'name': 'summary_concise', 'passed': False, 'detail': f'could not read output.txt: {err}'})
    else:
        word_count = len(re.findall(r'\b\w+\b', text))
        passed = word_count <= 80
        checks.append({'name': 'summary_concise', 'passed': passed, 'detail': f'word count: {word_count}'})
except Exception as e:
    checks.append({'name': 'summary_concise', 'passed': False, 'detail': f'error checking length: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
result = {
    'passed': passed_count == len(checks),
    'score': score,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False))