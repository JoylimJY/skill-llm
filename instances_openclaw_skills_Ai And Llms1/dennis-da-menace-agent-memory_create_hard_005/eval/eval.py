import json
import os
from pathlib import Path

checks = []
workspace = Path.cwd()
summary_path = workspace / 'memory_summary.txt'
db_path = Path.home() / '.agent-memory' / 'memory.db'

# Check 1: summary file exists and is non-empty
try:
    if summary_path.exists():
        text = summary_path.read_text(encoding='utf-8', errors='replace')
        passed = len(text.strip()) > 0
        detail = 'memory_summary.txt exists and is non-empty' if passed else 'memory_summary.txt is empty'
    else:
        passed = False
        detail = 'memory_summary.txt is missing'
except Exception as e:
    passed = False
    detail = f'Could not read memory_summary.txt: {e}'
checks.append({'name': 'summary_file', 'passed': passed, 'detail': detail})

# Check 2: summary mentions at least one durable fact from inputs
try:
    if summary_path.exists():
        text = summary_path.read_text(encoding='utf-8', errors='replace').lower()
        fact_hits = [
            'persistent across sessions' in text,
            'lessons learned' in text,
            'default' in text and 'memory.db' in text,
            'fastapi' in text,
            'redis' in text,
        ]
        passed = any(fact_hits)
        detail = 'summary includes at least one recognizable durable fact' if passed else 'summary does not include expected facts'
    else:
        passed = False
        detail = 'memory_summary.txt is missing'
except Exception as e:
    passed = False
    detail = f'Could not inspect summary content: {e}'
checks.append({'name': 'summary_content', 'passed': passed, 'detail': detail})

# Check 3: summary mentions at least one lesson from session log
try:
    if summary_path.exists():
        text = summary_path.read_text(encoding='utf-8', errors='replace').lower()
        lesson_hits = [
            'loading recent lessons first' in text,
            'avoid repeating the same mistake' in text,
            'after failures' in text,
        ]
        passed = any(lesson_hits)
        detail = 'summary includes a lesson learned from the session log' if passed else 'summary does not include an expected lesson'
    else:
        passed = False
        detail = 'memory_summary.txt is missing'
except Exception as e:
    passed = False
    detail = f'Could not inspect lesson text: {e}'
checks.append({'name': 'lesson_content', 'passed': passed, 'detail': detail})

# Check 4: database file exists in the expected default location
try:
    if db_path.exists():
        passed = db_path.is_file() and db_path.stat().st_size > 0
        detail = f'database found at {db_path}' if passed else f'database path exists but is not a non-empty file: {db_path}'
    else:
        passed = False
        detail = f'database missing at expected path: {db_path}'
except Exception as e:
    passed = False
    detail = f'Could not inspect database path: {e}'
checks.append({'name': 'database_exists', 'passed': passed, 'detail': detail})

# Check 5: workspace marker file still exists to confirm task inputs were used
try:
    marker = workspace / 'marker.json'
    if marker.exists():
        data = json.loads(marker.read_text(encoding='utf-8', errors='replace'))
        passed = isinstance(data, dict) and data.get('marker') == 'AGENT_MEMORY_TASK_V1'
        detail = 'marker.json contains the expected marker' if passed else 'marker.json content is unexpected'
    else:
        passed = False
        detail = 'marker.json is missing'
except Exception as e:
    passed = False
    detail = f'Could not verify marker.json: {e}'
checks.append({'name': 'input_marker', 'passed': passed, 'detail': detail})

score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
result = {'passed': all(c['passed'] for c in checks), 'score': score, 'checks': checks}
print(json.dumps(result))
