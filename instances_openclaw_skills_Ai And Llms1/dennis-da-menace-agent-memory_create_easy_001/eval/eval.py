import json
import os
import sqlite3
import re
from pathlib import Path
import sys

def normalize(text):
    return re.sub(r'[^a-z0-9]+', ' ', (text or '').lower()).strip()

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

# Check 1: markdown summary exists and contains expected marker concepts
try:
    summary_path = workspace / 'memory_summary.md'
    if not summary_path.exists():
        checks.append({
            'name': 'summary_exists',
            'passed': False,
            'detail': 'memory_summary.md was not found.'
        })
    else:
        text = summary_path.read_text(encoding='utf-8', errors='ignore')
        ntext = normalize(text)
        required_terms = ['aurora', 'python', 'taylor', 'engineer', 'save memory']
        missing = [t for t in required_terms if normalize(t) not in ntext]
        passed = len(missing) == 0
        checks.append({
            'name': 'summary_content',
            'passed': passed,
            'detail': 'Missing terms: ' + ', '.join(missing) if missing else 'All required concepts present.'
        })
except Exception as e:
    checks.append({
        'name': 'summary_content',
        'passed': False,
        'detail': f'Error reading summary: {e}'
    })

# Check 2: memory database exists at default location and is readable
try:
    db_path = Path.home() / '.agent-memory' / 'memory.db'
    if not db_path.exists():
        checks.append({
            'name': 'memory_db_exists',
            'passed': False,
            'detail': f'Database not found at {db_path}'
        })
    else:
        ok = False
        detail = 'Database file exists.'
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [t[0].lower() for t in tables]
            ok = len(table_names) > 0
            detail = 'Tables found: ' + ', '.join(table_names[:10]) if ok else 'No tables found in database.'
            conn.close()
        except Exception as e:
            detail = f'Could not inspect database: {e}'
        checks.append({
            'name': 'memory_db_readable',
            'passed': ok,
            'detail': detail
        })
except Exception as e:
    checks.append({
        'name': 'memory_db_exists',
        'passed': False,
        'detail': f'Error checking database: {e}'
    })

# Check 3: input marker file exists to ensure deterministic task inputs were generated
try:
    marker_path = workspace / 'session_notes.txt'
    if not marker_path.exists():
        checks.append({
            'name': 'input_marker_exists',
            'passed': False,
            'detail': 'session_notes.txt is missing.'
        })
    else:
        text = marker_path.read_text(encoding='utf-8', errors='ignore')
        passed = 'MARKER_SESSION=alpha' in text and 'Taylor' in text and 'Aurora' in text
        checks.append({
            'name': 'input_marker_content',
            'passed': passed,
            'detail': 'Marker file contains expected deterministic content.' if passed else 'Marker content did not match expected values.'
        })
except Exception as e:
    checks.append({
        'name': 'input_marker_content',
        'passed': False,
        'detail': f'Error reading marker file: {e}'
    })

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
result = {
    'passed': passed_count == len(checks) and len(checks) > 0,
    'score': score,
    'checks': checks,
}
print(json.dumps(result))
