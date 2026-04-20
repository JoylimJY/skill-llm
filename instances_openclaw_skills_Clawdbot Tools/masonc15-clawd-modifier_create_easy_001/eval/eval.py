import json
import os
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s: str) -> str:
    return ''.join(ch.lower() for ch in s if ch.isalnum())


def main():
    import sys
    ws = Path(sys.argv[1])
    checks = []

    # Check 1: marker file exists and contains expected markers
    try:
        marker_path = ws / 'markers' / 'clawd_task_marker.txt'
        if marker_path.exists():
            text = marker_path.read_text(encoding='utf-8', errors='replace')
            norm_text = normalize(text)
            # Fixed: use normalized strings without underscores
            passed = ('clawdtaskmarker' in norm_text) and ('expectedcolorblue' in norm_text) and ('expectedvariantwitharms' in norm_text)
            detail = 'marker file present and contains expected markers' if passed else f'marker content mismatch: {text[:200]!r}'
        else:
            passed = False
            detail = 'marker file missing'
    except Exception as e:
        passed = False
        detail = f'error checking marker file: {e}'
    checks.append({'name': 'marker_file', 'passed': passed, 'detail': detail})

    # Check 2: input spec exists and is parseable
    try:
        spec_path = ws / 'input_spec.json'
        if spec_path.exists():
            data = json.loads(spec_path.read_text(encoding='utf-8', errors='replace'))
            passed = normalize(str(data.get('target_color', ''))) == 'blue' and normalize(str(data.get('target_variant', ''))) == 'witharms'
            detail = 'input_spec.json contains expected task parameters' if passed else f'unexpected spec values: {data}'
        else:
            passed = False
            detail = 'input_spec.json missing'
    except Exception as e:
        passed = False
        detail = f'error checking input_spec.json: {e}'
    checks.append({'name': 'input_spec', 'passed': passed, 'detail': detail})

    # Check 3: expected output files exist (flexible - accept JSON settings OR SVG art)
    try:
        # Look for color settings file (JSON)
        settings_found = False
        settings_content = None
        for f in ws.rglob('*.json'):
            if 'clawd' in f.name.lower() and 'color' in f.name.lower():
                settings_found = True
                settings_content = f.read_text(encoding='utf-8', errors='replace')
                break
        
        # Look for mascot art file (SVG)
        art_found = False
        art_content = None
        for f in ws.rglob('*.svg'):
            if 'clawd' in f.name.lower():
                art_found = True
                art_content = f.read_text(encoding='utf-8', errors='replace')
                break
        
        # Check content if files found
        settings_valid = False
        art_valid = False
        
        if settings_found and settings_content:
            norm_settings = normalize(settings_content)
            settings_valid = ('blue' in norm_settings) and ('arm' in norm_settings)
        
        if art_found and art_content:
            norm_art = normalize(art_content)
            art_valid = ('blue' in norm_art) and ('arm' in norm_art)
        
        # Pass if at least one valid output file exists
        passed = (settings_found and settings_valid) or (art_found and art_valid)
        
        if passed:
            detail = 'output files exist and mention blue and arms'
        elif settings_found or art_found:
            detail = f'output files found but content does not mention required properties'
        else:
            detail = 'no clawd output files found (expected JSON settings or SVG art)'
    except Exception as e:
        passed = False
        detail = f'error checking output files: {e}'
    checks.append({'name': 'output_file', 'passed': passed, 'detail': detail})

    # Check 4: no unexpected crash-prone conditions; workspace should be readable
    try:
        files = list(ws.rglob('*'))
        passed = len(files) >= 2
        detail = f'workspace contains {len(files)} files/directories' if passed else 'workspace unexpectedly sparse'
    except Exception as e:
        passed = False
        detail = f'error listing workspace: {e}'
    checks.append({'name': 'workspace_readable', 'passed': passed, 'detail': detail})

    score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
    passed = all(c['passed'] for c in checks)

    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()