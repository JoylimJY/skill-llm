import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

try:
    out_path = workspace / 'article.md'
    if not out_path.exists():
        checks.append({'name': 'output_exists', 'passed': False, 'detail': 'article.md is missing'})
    else:
        text = out_path.read_text(encoding='utf-8', errors='replace')
        norm = re.sub(r'\s+', ' ', text.lower())
        checks.append({'name': 'output_exists', 'passed': True, 'detail': 'article.md exists'})
        checks.append({'name': 'has_title', 'passed': bool(re.search(r'^\s*#\s+.+', text, re.M)), 'detail': 'title line found' if re.search(r'^\s*#\s+.+', text, re.M) else 'missing markdown title'})
        checks.append({'name': 'keeps_core_facts', 'passed': all(k in norm for k in ['free books', 'internet access', 'quiet study space', 'reading clubs', 'workshops', 'volunteers']), 'detail': 'core facts appear preserved'})
        checks.append({'name': 'references_at_end', 'passed': 'reference' in norm and norm.rfind('reference') > len(norm) * 0.5, 'detail': 'references section appears near the end'})
except Exception as e:
    checks.append({'name': 'evaluation_error', 'passed': False, 'detail': f'exception during evaluation: {type(e).__name__}: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / max(len(checks), 1)
result = {'passed': passed_count == len(checks) and len(checks) > 0, 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
