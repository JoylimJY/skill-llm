import json
import os
import re
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def normalize(text):
    try:
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: a plausible mnemon output exists (at least one non-input artifact)
    try:
        files = [p for p in workspace.iterdir() if p.is_file()]
        input_names = {'session_notes.txt', 'memory_plan.json'}
        outputs = [p for p in files if p.name not in input_names]
        passed = len(outputs) > 0
        detail = f'found {len(outputs)} output file(s)' if passed else 'no output files found beyond generated inputs'
    except Exception as e:
        passed = False
        detail = f'failed to inspect workspace: {e}'
    checks.append({'name': 'output_file_present', 'passed': passed, 'detail': detail})

    # Check 2: at least one file mentions Northstar in a fuzzy way
    try:
        found = False
        hit_file = None
        for p in workspace.iterdir():
            if not p.is_file():
                continue
            if p.name in {'session_notes.txt', 'memory_plan.json'}:
                continue
            try:
                text = p.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            if 'northstar' in normalize(text):
                found = True
                hit_file = p.name
                break
        passed = found
        detail = f'northstar mention found in {hit_file}' if found else 'no non-input file contained a Northstar-like mention'
    except Exception as e:
        passed = False
        detail = f'error while scanning files: {e}'
    checks.append({'name': 'northstar_mention', 'passed': passed, 'detail': detail})

    # Check 3: at least one file mentions a sensible memory category or summary hint
    try:
        target_words = ['preference', 'decision', 'insight', 'summary', 'recall']
        found = False
        hit = None
        for p in workspace.iterdir():
            if not p.is_file() or p.name in {'session_notes.txt', 'memory_plan.json'}:
                continue
            try:
                text = normalize(p.read_text(encoding='utf-8', errors='replace'))
            except Exception:
                continue
            if any(w in text for w in target_words):
                found = True
                hit = p.name
                break
        passed = found
        detail = f'category/summary hint found in {hit}' if found else 'no category or summary hint detected in outputs'
    except Exception as e:
        passed = False
        detail = f'error while validating categories: {e}'
    checks.append({'name': 'category_or_summary_hint', 'passed': passed, 'detail': detail})

    score = 0.0
    try:
        if checks:
            score = sum(1 for c in checks if c['passed']) / len(checks)
    except Exception:
        score = 0.0

    result = {'passed': all(c['passed'] for c in checks), 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
