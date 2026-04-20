import json
import os
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def normalize(s: str) -> str:
    import re
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return ' '.join(s.split())


def main(workspace_dir: str):
    checks = []
    ws = Path(workspace_dir)

    # Check 1: summary.txt exists
    try:
        summary_path = ws / 'summary.txt'
        exists = summary_path.exists()
        checks.append({
            'name': 'summary_exists',
            'passed': bool(exists),
            'detail': 'summary.txt found' if exists else 'summary.txt is missing'
        })
    except Exception as e:
        checks.append({
            'name': 'summary_exists',
            'passed': False,
            'detail': f'error checking file existence: {e}'
        })

    # Check 2: content mentions pincer and security-related concepts
    try:
        summary_path = ws / 'summary.txt'
        text = None
        err = None
        if summary_path.exists():
            try:
                text = summary_path.read_text(encoding='utf-8', errors='replace')
            except Exception as e:
                err = str(e)
        if text is None:
            checks.append({
                'name': 'summary_content',
                'passed': False,
                'detail': f'could not read summary.txt: {err or "missing"}'
            })
        else:
            norm = normalize(text)
            has_pincer = 'pincer' in norm
            has_security = any(k in norm for k in ['security first', 'security', 'scan', 'malware', 'prompt injection', 'suspicious patterns', 'binaries', 'bundled binaries'])
            passed = has_pincer and has_security
            detail = 'contains pincer and security-related wording' if passed else 'missing required pincer/security wording'
            checks.append({
                'name': 'summary_content',
                'passed': passed,
                'detail': detail
            })
    except Exception as e:
        checks.append({
            'name': 'summary_content',
            'passed': False,
            'detail': f'error reading or analyzing summary.txt: {e}'
        })

    # Check 3: concise length
    try:
        summary_path = ws / 'summary.txt'
        if summary_path.exists():
            try:
                text = summary_path.read_text(encoding='utf-8', errors='replace')
                words = [w for w in text.split() if w.strip()]
                passed = len(words) <= 40
                checks.append({
                    'name': 'summary_concise',
                    'passed': passed,
                    'detail': f'word count is {len(words)} (<= 40 required)' if passed else f'word count is {len(words)} (> 40)'
                })
            except Exception as e:
                checks.append({
                    'name': 'summary_concise',
                    'passed': False,
                    'detail': f'could not measure length: {e}'
                })
        else:
            checks.append({
                'name': 'summary_concise',
                'passed': False,
                'detail': 'summary.txt missing, cannot verify length'
            })
    except Exception as e:
        checks.append({
            'name': 'summary_concise',
            'passed': False,
            'detail': f'error verifying length: {e}'
        })

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    result = {
        'passed': passed_count == total and total > 0,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
