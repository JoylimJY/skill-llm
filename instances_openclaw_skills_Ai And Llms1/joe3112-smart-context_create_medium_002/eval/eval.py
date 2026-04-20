import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def normalize(text):
    return re.sub(r'[^a-z0-9]+', '', text.lower()) if text is not None else ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    output_dir = workspace / 'output'
    summary_path = output_dir / 'project_notes.md'
    meta_path = output_dir / 'metadata.json'

    try:
        summary_text, error = safe_read(summary_path)
        if error:
            checks.append({'name': 'summary_exists_and_contains_key_info', 'passed': False, 'detail': f'Could not read summary: {error}'})
        else:
            summary_ok = all(token in summary_text.lower() for token in ['project orion', 'team blue', 'v2.4.1', '87', '143', '2'])
            checks.append({'name': 'summary_exists_and_contains_key_info', 'passed': summary_ok, 'detail': 'Found summary with required info.' if summary_ok else 'Summary missing required info.'})
    except Exception as e:
        checks.append({'name': 'summary_exists_and_contains_key_info', 'passed': False, 'detail': f'Could not read summary: {e}'})

    try:
        meta_text, error = safe_read(meta_path)
        if error:
            checks.append({'name': 'metadata_exists_and_has_markers', 'passed': False, 'detail': f'Could not parse metadata: {error}'})
        else:
            meta = json.loads(meta_text)
            marker_ok = normalize(' '.join(meta.get('markers', [])))
            expected_markers = ['orion2025alpha', 'csvmark19', 'jsonmark77']
            meta_ok = all(normalize(m) in marker_ok for m in expected_markers) and meta.get('project', '').lower() == 'project orion'
            checks.append({'name': 'metadata_exists_and_has_markers', 'passed': meta_ok, 'detail': 'Metadata contains expected markers and project name.' if meta_ok else 'Metadata missing expected markers or project name.'})
    except Exception as e:
        checks.append({'name': 'metadata_exists_and_has_markers', 'passed': False, 'detail': f'Could not parse metadata: {e}'})

    try:
        summary_text, error = safe_read(summary_path)
        if error:
            checks.append({'name': 'summary_is_concise', 'passed': False, 'detail': 'Summary file missing.'})
        else:
            concise_ok = len(summary_text.split()) <= 120
            checks.append({'name': 'summary_is_concise', 'passed': concise_ok, 'detail': f'Summary word count: {len(summary_text.split())}.' if summary_text else 'Summary file missing.'})
    except Exception as e:
        checks.append({'name': 'summary_is_concise', 'passed': False, 'detail': f'Could not inspect summary length: {e}'})

    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks) if checks else 0.0
    result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()