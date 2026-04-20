import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def fuzzy_contains(text, needles):
    if text is None:
        return False
    t = re.sub(r'\s+', ' ', text.lower())
    return all(n.lower() in t for n in needles)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    export_dir = Path('/home/celluloid/.openclaw/workspace/stl-exports')

    # Check 1: marker input file exists and contains marker
    try:
        p = workspace / 'workspace_marker.txt'
        if p.exists():
            txt = p.read_text(encoding='utf-8', errors='ignore')
            ok = 'AI_3D_GENERATOR_MARKER::DRONE_TASK::1337' in txt
            checks.append({'name': 'input marker file', 'passed': ok, 'detail': 'marker present' if ok else 'marker missing'})
        else:
            checks.append({'name': 'input marker file', 'passed': False, 'detail': 'workspace_marker.txt missing'})
    except Exception as e:
        checks.append({'name': 'input marker file', 'passed': False, 'detail': f'error: {e}'})

    # Check 2: prompt template file exists and mentions trimesh + STL export
    try:
        p = workspace / 'prompts' / '3d-generator.txt'
        if p.exists():
            txt = p.read_text(encoding='utf-8', errors='ignore')
            ok = fuzzy_contains(txt, ['trimesh', 'stl', 'export'])
            checks.append({'name': 'prompt template', 'passed': ok, 'detail': 'contains trimesh/STL/export' if ok else 'missing required terms'})
        else:
            checks.append({'name': 'prompt template', 'passed': False, 'detail': 'prompts/3d-generator.txt missing'})
    except Exception as e:
        checks.append({'name': 'prompt template', 'passed': False, 'detail': f'error: {e}'})

    # Check 3: at least one STL file exported
    try:
        stls = []
        if export_dir.exists():
            stls = [p for p in export_dir.glob('*.stl') if p.is_file()]
        ok = len(stls) > 0
        detail = f'{len(stls)} STL file(s) found' if ok else 'no STL files found in export dir'
        checks.append({'name': 'stl export', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'stl export', 'passed': False, 'detail': f'error: {e}'})

    # Check 4: exported STL is non-trivial size
    try:
        ok = False
        detail = 'no candidate STL'
        if export_dir.exists():
            for p in export_dir.glob('*.stl'):
                try:
                    size = p.stat().st_size
                    if size > 1024:
                        ok = True
                        detail = f'{p.name} size={size}'
                        break
                except Exception:
                    continue
        checks.append({'name': 'stl nontrivial size', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'stl nontrivial size', 'passed': False, 'detail': f'error: {e}'})

    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks) if checks else 0.0
    result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
    print(json.dumps(result))

if __name__ == '__main__':
    main()
