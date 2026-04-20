import json
from pathlib import Path

checks = []
workspace = Path(__import__('sys').argv[1])

try:
    out_path = workspace / 'output.txt'
    exists = out_path.exists()
    detail = 'output.txt exists' if exists else 'output.txt is missing'
    checks.append({'name': 'output_file_exists', 'passed': exists, 'detail': detail})
except Exception as e:
    checks.append({'name': 'output_file_exists', 'passed': False, 'detail': f'error checking output.txt: {e}'})

try:
    content = ''
    if (workspace / 'output.txt').exists():
        content = (workspace / 'output.txt').read_text(encoding='utf-8', errors='replace')
    norm = ''.join(ch.lower() for ch in content if ch.isalnum() or ch.isspace())
    required = ['deepseekr1agent', 'effective', 'content', 'creator']
    passed = all(term in norm.replace(' ', '') if term == 'deepseekr1agent' else term in norm for term in required)
    detail = 'contains required tagline concepts' if passed else f'content did not clearly include required concepts: {content[:200]!r}'
    checks.append({'name': 'tagline_content', 'passed': passed, 'detail': detail})
except Exception as e:
    checks.append({'name': 'tagline_content', 'passed': False, 'detail': f'error reading output.txt: {e}'})

try:
    marker_path = workspace / 'input_marker.txt'
    marker_exists = marker_path.exists()
    checks.append({'name': 'input_marker_exists', 'passed': marker_exists, 'detail': 'input_marker.txt exists' if marker_exists else 'input_marker.txt is missing'})
except Exception as e:
    checks.append({'name': 'input_marker_exists', 'passed': False, 'detail': f'error checking marker file: {e}'})

score = (sum(1 for c in checks if c.get('passed')) / len(checks)) if checks else 0.0
result = {'passed': all(c.get('passed') for c in checks), 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
