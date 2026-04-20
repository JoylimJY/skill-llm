import json
import os
import re
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: A markdown build-session note exists
    try:
        md_files = list(workspace.glob('**/*.md'))
        candidates = []
        for p in md_files:
            try:
                txt = p.read_text(encoding='utf-8')
            except Exception:
                continue
            n = normalize(txt)
            if 'build session' in n and 'what i built' in n and 'key insights' in n and 'git' in n:
                candidates.append(p)
        passed = len(candidates) > 0
        detail = f'Found {len(candidates)} candidate markdown note(s).' if passed else f'No markdown note matched required sections. Markdown files found: {len(md_files)}.'
    except Exception as e:
        passed = False
        detail = f'Error while searching markdown notes: {e}'
    checks.append({'name': 'markdown note with required sections', 'passed': passed, 'detail': detail})

    # Check 2: Note should reference at least one provided marker or context item
    try:
        marker_terms = ['build_session_marker_alpha', 'build_session_marker_beta', 'build_session_marker_gamma', 'heartbeat']
        found = False
        matched_file = None
        for p in workspace.glob('**/*.md'):
            try:
                txt = p.read_text(encoding='utf-8').lower()
            except Exception:
                continue
            if any(term in txt for term in marker_terms):
                found = True
                matched_file = p.name
                break
        passed = found
        detail = f'Marker/context reference found in {matched_file}.' if passed else 'No marker or context reference found in any markdown note.'
    except Exception as e:
        passed = False
        detail = f'Error checking marker references: {e}'
    checks.append({'name': 'references workspace context', 'passed': passed, 'detail': detail})

    # Check 3: Title/date-like header appears near top of the note
    try:
        ok = False
        detail = 'No matching header found.'
        for p in workspace.glob('**/*.md'):
            try:
                lines = p.read_text(encoding='utf-8').splitlines()
            except Exception:
                continue
            head = '\n'.join(lines[:8])
            if re.search(r'^#\s+build session', head, flags=re.I | re.M) or re.search(r'^##\s+build session', head, flags=re.I | re.M):
                ok = True
                detail = f'Header appears near top in {p.name}.'
                break
        passed = ok
    except Exception as e:
        passed = False
        detail = f'Error checking header placement: {e}'
    checks.append({'name': 'session header near top', 'passed': passed, 'detail': detail})

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
