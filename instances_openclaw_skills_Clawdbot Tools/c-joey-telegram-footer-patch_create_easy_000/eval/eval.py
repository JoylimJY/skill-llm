import json
import os
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        text = text or ''
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
    except Exception:
        return ''


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def extract_all_text(data):
    """Recursively extract all text values from a nested structure."""
    if isinstance(data, dict):
        texts = []
        for value in data.values():
            texts.extend(extract_all_text(value))
        return texts
    elif isinstance(data, list):
        texts = []
        for item in data:
            texts.extend(extract_all_text(item))
        return texts
    elif isinstance(data, str):
        return [data]
    else:
        return [str(data)]


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    expected_files = ['release_note.txt', 'verification_summary.json', 'README.md']

    # Check 1: files exist
    missing = []
    try:
        for name in expected_files:
            if not (workspace / name).is_file():
                missing.append(name)
        passed = len(missing) == 0
        detail = 'All required files present.' if passed else f'Missing: {", ".join(missing)}'
    except Exception as e:
        passed = False
        detail = f'Error checking file existence: {e}'
    checks.append({'name': 'required_files_exist', 'passed': passed, 'detail': detail})

    # Check 2: release_note.txt content
    try:
        text, err = safe_read(workspace / 'release_note.txt')
        if text is None:
            passed = False
            detail = f'Could not read release_note.txt: {err}'
        else:
            n = normalize(text)
            markers = ['model think context', 'dry run', 'backup', 'rollback', 'restart']
            found = [m for m in markers if normalize(m) in n]
            passed = len(found) >= 4
            detail = f'Found markers: {found}' if passed else f'Only found markers: {found}'
    except Exception as e:
        passed = False
        detail = f'Error validating release_note.txt: {e}'
    checks.append({'name': 'release_note_mentions_key_flow', 'passed': passed, 'detail': detail})

    # Check 3: verification_summary.json structure/content
    try:
        raw, err = safe_read(workspace / 'verification_summary.json')
        if raw is None:
            passed = False
            detail = f'Could not read verification_summary.json: {err}'
        else:
            try:
                data = json.loads(raw)
                # Extract all text from the JSON structure (handles nested structures)
                all_texts = extract_all_text(data)
                full_text = ' '.join(all_texts)
                n = normalize(full_text)
                
                # Check for marker phrase anywhere in the JSON
                has_marker = 'model think context' in n
                
                # Check for deployment flow keywords anywhere in the JSON
                required_keywords = ['dry', 'backup', 'rollback', 'restart']
                has_all_keywords = all(k in n for k in required_keywords)
                
                passed = has_marker and has_all_keywords
                detail = 'JSON contains marker_phrase and deployment flow keywords.' if passed else f'JSON validation failed. Has marker: {has_marker}, Has all keywords: {has_all_keywords}'
            except Exception as e:
                passed = False
                detail = f'Invalid JSON: {e}'
    except Exception as e:
        passed = False
        detail = f'Error validating verification_summary.json: {e}'
    checks.append({'name': 'verification_summary_json_valid', 'passed': passed, 'detail': detail})

    # Check 4: README quality hint
    try:
        text, err = safe_read(workspace / 'README.md')
        if text is None:
            passed = False
            detail = f'Could not read README.md: {err}'
        else:
            n = normalize(text)
            passed = ('telegram' in n) and ('footer' in n) and ('patch' in n)
            detail = 'README covers telegram footer patch.' if passed else 'README missing one or more expected concepts.'
    except Exception as e:
        passed = False
        detail = f'Error validating README.md: {e}'
    checks.append({'name': 'readme_mentions_feature', 'passed': passed, 'detail': detail})

    score = 0.0
    try:
        score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
    except Exception:
        score = 0.0

    result = {
        'passed': score == 1.0,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()