import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, f'failed to read {path}: {e}'


def fuzzy_has(text, needles):
    try:
        t = re.sub(r'[^a-z0-9]+', ' ', (text or '').lower()).strip()
        return all(re.sub(r'[^a-z0-9]+', ' ', n.lower()).strip() in t for n in needles)
    except Exception:
        return False


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    try:
        config_path = workspace / '.openclaw' / 'safety-checks.yaml'
        if config_path.exists():
            text = config_path.read_text(encoding='utf-8', errors='ignore')
            passed = fuzzy_has(text, ['model', 'expected', 'anthropic opus 4 5 20251101']) and fuzzy_has(text, ['fallbacks', 'model', 'storage'])
            detail = 'Primary config found with model expectation and fallback sections.' if passed else 'Primary config missing expected model or fallback content.'
        else:
            passed = False
            detail = 'Missing .openclaw/safety-checks.yaml.'
    except Exception as e:
        passed = False
        detail = f'Error checking primary config: {e}'
    checks.append({'name': 'primary_config', 'passed': passed, 'detail': detail})

    try:
        cache_path = workspace / '.openclaw' / 'cache' / 'staleness.log'
        if cache_path.exists():
            raw = cache_path.read_text(encoding='utf-8', errors='ignore')
            passed = fuzzy_has(raw, ['safety checks baseline']) or ('SAFETY-CHECKS-BASELINE' in raw.upper())
            detail = 'Cache metadata marker detected.' if passed else 'Cache marker content not found.'
        else:
            passed = False
            detail = 'Missing cache staleness log.'
    except Exception as e:
        passed = False
        detail = f'Error checking cache log: {e}'
    checks.append({'name': 'cache_marker', 'passed': passed, 'detail': detail})

    try:
        lock_path = workspace / '.openclaw' / 'safety-checks.lock'
        temp1 = workspace / 'output' / 'safety' / 'temp-leak-1.log'
        temp2 = workspace / 'output' / 'safety' / 'temp-leak-2.log'
        lock_exists = lock_path.exists()
        temps_exist = temp1.exists() and temp2.exists()
        passed = lock_exists and temps_exist
        detail = 'Lock file and temp files are present as baseline inputs.' if passed else 'Expected baseline lock/temp leakage files are missing.'
    except Exception as e:
        passed = False
        detail = f'Error checking baseline leakage files: {e}'
    checks.append({'name': 'baseline_leakage_inputs', 'passed': passed, 'detail': detail})

    try:
        out_dir = workspace / 'output' / 'safety'
        passed = out_dir.exists() and out_dir.is_dir()
        detail = 'Output directory exists.' if passed else 'Missing output/safety directory.'
    except Exception as e:
        passed = False
        detail = f'Error checking output directory: {e}'
    checks.append({'name': 'output_directory', 'passed': passed, 'detail': detail})

    try:
        total = len(checks)
        passed_count = sum(1 for c in checks if c['passed'])
        score = passed_count / total if total else 0.0
        passed = passed_count == total
    except Exception:
        score = 0.0
        passed = False

    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': f'unhandled error: {e}'}]}))
