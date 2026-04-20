from pathlib import Path
import json
import re
import string
import sys


def norm(text: str) -> str:
    text = text.lower()
    text = ''.join(ch for ch in text if ch not in string.punctuation)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

checks = []
workspace = Path(sys.argv[1])
out = workspace / 'review_note.md'
source = workspace / 'SKILL.md'

# Check 1: output exists
try:
    exists = out.exists()
    checks.append({
        'name': 'output_file_exists',
        'passed': bool(exists),
        'detail': 'review_note.md found' if exists else 'review_note.md is missing'
    })
except Exception as e:
    checks.append({'name': 'output_file_exists', 'passed': False, 'detail': f'Error checking file existence: {e}'})

# Check 2: readable content and required structure
content = ''
try:
    content = out.read_text(encoding='utf-8') if out.exists() else ''
    n = norm(content)
    has_summary = 'summary' in n
    has_principles = 'principles' in n
    has_recommendation = 'recommendation' in n
    bullet_count = len(re.findall(r'(?m)^\s*[-*+]\s+', content))
    passed = has_summary and has_principles and has_recommendation and bullet_count == 3
    detail = f'summary={has_summary}, principles={has_principles}, recommendation={has_recommendation}, bullets={bullet_count}'
    checks.append({'name': 'structure_and_bullets', 'passed': passed, 'detail': detail})
except Exception as e:
    checks.append({'name': 'structure_and_bullets', 'passed': False, 'detail': f'Error reading/parsing review_note.md: {e}'})

# Check 3: content aligns with source principles
try:
    src = source.read_text(encoding='utf-8') if source.exists() else ''
    candidates = [
        'unclear incentives',
        'systems drift',
        'reversible actions',
        'information compounds',
        'reliability and candor',
        'disagree when it matters',
        'slow down when stakes are high'
    ]
    matches = sum(1 for c in candidates if c.lower() in content.lower())
    passed = matches >= 3 and src != ''
    detail = f'matched_source_signals={matches}'
    checks.append({'name': 'source_alignment', 'passed': passed, 'detail': detail})
except Exception as e:
    checks.append({'name': 'source_alignment', 'passed': False, 'detail': f'Error validating source alignment: {e}'})

score = sum(1 for c in checks if c.get('passed')) / len(checks) if checks else 0.0
passed = all(c.get('passed') for c in checks) if checks else False
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))
