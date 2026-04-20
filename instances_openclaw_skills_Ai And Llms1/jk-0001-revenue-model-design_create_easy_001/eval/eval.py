import json
import os
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return ""


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: output file exists
    try:
        out = workspace / 'revenue_model_brief.txt'
        exists = out.exists()
        checks.append({
            'name': 'output_file_exists',
            'passed': bool(exists),
            'detail': 'revenue_model_brief.txt found' if exists else 'revenue_model_brief.txt is missing'
        })
    except Exception as e:
        checks.append({'name': 'output_file_exists', 'passed': False, 'detail': f'Exception while checking file existence: {e}'})

    # Check 2: contains primary/secondary/opportunistic stream language
    try:
        text = out.read_text(encoding='utf-8') if out.exists() else ''
        n = normalize(text)
        required = ['primary', 'secondary', 'opportunistic']
        passed = all(term in n for term in required)
        checks.append({
            'name': 'stream_structure',
            'passed': passed,
            'detail': 'Contains primary, secondary, and opportunistic revenue stream language' if passed else 'Missing one or more required stream labels'
        })
    except Exception as e:
        checks.append({'name': 'stream_structure', 'passed': False, 'detail': f'Exception while reading output: {e}'})

    # Check 3: contains a 12-month projection reference and at least one numeric month mention
    try:
        text = out.read_text(encoding='utf-8') if out.exists() else ''
        n = normalize(text)
        has_projection = ('12 month' in n or '12 months' in n or 'one year' in n) and bool(re.search(r'\bmonth\s*1\b|\bmonth\s*12\b', n))
        checks.append({
            'name': 'projection_present',
            'passed': bool(has_projection),
            'detail': 'Includes a basic 12-month projection' if has_projection else 'No clear 12-month projection language detected'
        })
    except Exception as e:
        checks.append({'name': 'projection_present', 'passed': False, 'detail': f'Exception while validating projection: {e}'})

    # Check 4: references the input marker content in some form
    try:
        text = out.read_text(encoding='utf-8') if out.exists() else ''
        n = normalize(text)
        marker_ok = ('solo biz 42' in n or 'freelancers' in n or 'productivity templates' in n)
        checks.append({
            'name': 'input_reference',
            'passed': bool(marker_ok),
            'detail': 'Output appears to reference the provided business context' if marker_ok else 'No clear reference to the input file context'
        })
    except Exception as e:
        checks.append({'name': 'input_reference', 'passed': False, 'detail': f'Exception while checking input reference: {e}'})

    score = (sum(1 for c in checks if c.get('passed')) / len(checks)) if checks else 0.0
    result = {
        'passed': all(c.get('passed') for c in checks) if checks else False,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
