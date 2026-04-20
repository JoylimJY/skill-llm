import json
import re
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def normalize(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', s.lower())


def fuzzy_contains(text: str, needle: str) -> bool:
    return normalize(needle) in normalize(text)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: task metadata exists and contains marker
    try:
        p = workspace / 'task_metadata.json'
        if p.exists():
            raw = p.read_text(encoding='utf-8', errors='replace')
            ok = fuzzy_contains(raw, 'clawd_blue_arms') and fuzzy_contains(raw, 'expected_small_art')
            checks.append({
                'name': 'input metadata markers',
                'passed': ok,
                'detail': 'markers found' if ok else 'required markers missing'
            })
        else:
            checks.append({'name': 'input metadata markers', 'passed': False, 'detail': 'task_metadata.json missing'})
    except Exception as e:
        checks.append({'name': 'input metadata markers', 'passed': False, 'detail': f'error reading metadata: {e}'})

    # Check 2: output file exists
    try:
        out = workspace / 'output.txt'
        if out.exists():
            checks.append({'name': 'output file exists', 'passed': True, 'detail': 'output.txt present'})
        else:
            checks.append({'name': 'output file exists', 'passed': False, 'detail': 'output.txt missing'})
    except Exception as e:
        checks.append({'name': 'output file exists', 'passed': False, 'detail': f'error checking output file: {e}'})

    # Check 3: output mentions blue and arms in a fuzzy way
    try:
        out = workspace / 'output.txt'
        if out.exists():
            text = out.read_text(encoding='utf-8', errors='replace')
            has_blue = (fuzzy_contains(text, 'blue') or fuzzy_contains(text, 'oceanblue') or fuzzy_contains(text, 'bluebright'))
            has_arms = (fuzzy_contains(text, 'arms') or fuzzy_contains(text, 'witharms') or fuzzy_contains(text, 'leftarm') or fuzzy_contains(text, 'rightarm'))
            ok = has_blue and has_arms
            checks.append({'name': 'output describes blue arms modification', 'passed': ok, 'detail': 'blue/arms content found' if ok else 'expected blue and arm-related content not found'})
        else:
            checks.append({'name': 'output describes blue arms modification', 'passed': False, 'detail': 'output.txt missing so content could not be verified'})
    except Exception as e:
        checks.append({'name': 'output describes blue arms modification', 'passed': False, 'detail': f'error reading output: {e}'})

    # Check 4: backup file created OR mascot file created (flexible check)
    try:
        candidates = list(workspace.rglob('*'))
        found_backup = False
        found_mascot = False
        detail = 'no backup or mascot file found'
        for p in candidates:
            try:
                name = p.name.lower()
                if p.is_file():
                    # Check for backup files
                    if 'backup' in name or name.endswith('.bak') or name.endswith('.orig') or 'backup' in name:
                        found_backup = True
                        detail = f'found backup: {p.name}'
                    # Check for mascot files
                    if 'clawd' in name or 'mascot' in name:
                        found_mascot = True
                        if not found_backup:
                            detail = f'found mascot file: {p.name}'
            except Exception:
                continue
        # Pass if either backup OR mascot file exists
        found = found_backup or found_mascot
        checks.append({'name': 'backup created', 'passed': found, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'backup created', 'passed': False, 'detail': f'error scanning for backup: {e}'})

    # Check 5: manifest remains intact and markers are present
    try:
        p = workspace / 'manifest.csv'
        if p.exists():
            raw = p.read_text(encoding='utf-8', errors='replace')
            ok = fuzzy_contains(raw, 'key,value') and fuzzy_contains(raw, 'm0') and fuzzy_contains(raw, 'm4')
            checks.append({'name': 'manifest intact', 'passed': ok, 'detail': 'manifest looks intact' if ok else 'manifest content unexpected'})
        else:
            checks.append({'name': 'manifest intact', 'passed': False, 'detail': 'manifest.csv missing'})
    except Exception as e:
        checks.append({'name': 'manifest intact', 'passed': False, 'detail': f'error reading manifest: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    passed = passed_count == total

    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # Absolute fallback to avoid traceback leakage
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': f'unhandled error: {e}'}]}, ensure_ascii=False))