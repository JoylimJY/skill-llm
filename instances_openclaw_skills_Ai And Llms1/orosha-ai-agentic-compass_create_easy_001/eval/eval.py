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


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    try:
        out = workspace / 'memory' / 'agentic-compass.md'
        if out.exists():
            text = out.read_text(encoding='utf-8', errors='replace')
            n = normalize(text)
            required = [
                ('proactive', 'proactive'),
                ('deferred', 'deferred'),
                ('avoidance', 'avoidance'),
                ('ship', 'ship'),
            ]
            for name, needle in required:
                passed = needle in n
                checks.append({'name': f'contains_{name}', 'passed': passed, 'detail': f"searched for '{needle}'"})
        else:
            checks.append({'name': 'output_exists', 'passed': False, 'detail': 'memory/agentic-compass.md is missing'})
    except Exception as e:
        checks.append({'name': 'output_readable', 'passed': False, 'detail': f'error reading output: {e}'})

    try:
        daily = workspace / 'memory' / '2026-01-31.md'
        MEMORY = workspace / 'MEMORY.md'
        logs = workspace / 'logs.txt'
        found_marker = False
        for p in [daily, MEMORY, logs]:
            try:
                txt = p.read_text(encoding='utf-8', errors='replace')
                if 'AGENTIC_COMPASS_INPUT_READY' in txt or 'timeout' in txt.lower():
                    found_marker = True
            except Exception:
                pass
        checks.append({'name': 'input_markers_present', 'passed': found_marker, 'detail': 'verified deterministic marker content in generated inputs'})
    except Exception as e:
        checks.append({'name': 'input_markers_present', 'passed': False, 'detail': f'error checking inputs: {e}'})

    try:
        out = workspace / 'memory' / 'agentic-compass.md'
        passed = False
        if out.exists():
            text = out.read_text(encoding='utf-8', errors='replace')
            n = normalize(text)
            passed = ('one proactive' in n or 'proactive:' in n) and ('one deferred' in n or 'deferred:' in n) and ('one avoidance' in n or 'avoidance:' in n) and ('one ship' in n or 'ship:' in n)
        checks.append({'name': 'has_all_sections', 'passed': passed, 'detail': 'looked for the four requested plan sections'})
    except Exception as e:
        checks.append({'name': 'has_all_sections', 'passed': False, 'detail': f'error: {e}'})

    try:
        total = len(checks)
        passed_count = sum(1 for c in checks if c.get('passed'))
        score = passed_count / total if total else 0.0
        passed = all(c.get('passed') for c in checks)
        print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': str(e)}]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
