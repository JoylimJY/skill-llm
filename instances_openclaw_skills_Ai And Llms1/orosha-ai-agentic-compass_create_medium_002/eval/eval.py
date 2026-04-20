import json
import re
import sys
from pathlib import Path


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: output file exists
    try:
        out = workspace / 'memory' / 'agentic-compass.md'
        exists = out.exists()
        checks.append({
            'name': 'output_file_exists',
            'passed': bool(exists),
            'detail': 'Found memory/agentic-compass.md' if exists else 'Missing memory/agentic-compass.md'
        })
    except Exception as e:
        checks.append({'name': 'output_file_exists', 'passed': False, 'detail': f'Error checking file existence: {e}'})

    # Check 2: content includes all required sections/items, using fuzzy matching
    try:
        text, err = safe_read(out)
        if text is None:
            checks.append({'name': 'required_sections_and_items', 'passed': False, 'detail': f'Could not read output file: {err}'})
        else:
            n = norm(text)
            needles = [
                'proactive',
                'deferred',
                'avoidance',
                'ship',
                'score',
                'weakest axis',
            ]
            found = [needle for needle in needles if needle in n]
            passed = len(found) >= 5  # forgiving: allow slightly varied phrasing
            checks.append({
                'name': 'required_sections_and_items',
                'passed': passed,
                'detail': f'Found markers: {found}' if passed else f'Missing enough required concepts; found {found}'
            })
    except Exception as e:
        checks.append({'name': 'required_sections_and_items', 'passed': False, 'detail': f'Error parsing output: {e}'})

    # Check 3: output references local memory evidence markers
    try:
        text, err = safe_read(out)
        mem1, err1 = safe_read(workspace / 'memory' / '2026-01-31.md')
        mem2, err2 = safe_read(workspace / 'memory' / 'MEMORY.md')
        if text is None:
            checks.append({'name': 'references_local_memory', 'passed': False, 'detail': f'Could not read output file: {err}'})
        elif mem1 is None or mem2 is None:
            checks.append({'name': 'references_local_memory', 'passed': False, 'detail': f'Memory read error: {err1 or err2}'})
        else:
            n = norm(text)
            # At least one marker-related concept should appear in the plan
            evidence = any(x in n for x in ['completion rate', 'gateway diagnostic', 'moltbook api', 'osint graph analyzer'])
            checks.append({
                'name': 'references_local_memory',
                'passed': bool(evidence),
                'detail': 'Output references workspace-derived concepts' if evidence else 'Output does not appear to reflect the provided memory files'
            })
    except Exception as e:
        checks.append({'name': 'references_local_memory', 'passed': False, 'detail': f'Error evaluating references: {e}'})

    # Check 4: stdout-style metadata file if present? task only requires plan file, so verify it is non-empty and readable
    try:
        text, err = safe_read(out)
        if text is None:
            checks.append({'name': 'non_empty_output', 'passed': False, 'detail': f'Could not read output file: {err}'})
        else:
            passed = len(text.strip()) > 0
            checks.append({
                'name': 'non_empty_output',
                'passed': passed,
                'detail': f'Output length {len(text.strip())} characters' if passed else 'Output file is empty'
            })
    except Exception as e:
        checks.append({'name': 'non_empty_output', 'passed': False, 'detail': f'Error checking output size: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    result = {
        'passed': passed_count == total,
        'score': (passed_count / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
