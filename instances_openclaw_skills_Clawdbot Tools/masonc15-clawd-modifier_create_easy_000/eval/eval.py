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


def normalize(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', (s or '').lower())
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: input marker file exists and contains the deterministic marker
    try:
        notes_path = workspace / 'workspace' / 'notes.txt'
        if notes_path.exists():
            text = notes_path.read_text(encoding='utf-8', errors='ignore')
            passed = 'blue_and_arms' in text.lower()
            detail = 'marker found' if passed else 'marker missing'
        else:
            passed = False
            detail = 'workspace/notes.txt missing'
    except Exception as e:
        passed = False
        detail = f'error reading notes file: {e}'
    checks.append({'name': 'input_marker_present', 'passed': passed, 'detail': detail})

    # Check 2: spec file exists and indicates correct target
    try:
        spec_path = workspace / 'workspace' / 'spec.json'
        if spec_path.exists():
            spec = json.loads(spec_path.read_text(encoding='utf-8', errors='ignore'))
            passed = normalize(spec.get('expected_color')) == 'blue' and 'arm' in normalize(spec.get('expected_variant'))
            detail = 'spec looks correct' if passed else f'spec content unexpected: {spec}'
        else:
            passed = False
            detail = 'workspace/spec.json missing'
    except Exception as e:
        passed = False
        detail = f'error reading spec file: {e}'
    checks.append({'name': 'spec_valid', 'passed': passed, 'detail': detail})

    # Check 3: output file must exist (look for mascot-related files, not just output.txt)
    try:
        output_candidates = [
            workspace / 'output.txt',
            workspace / 'workspace' / 'output.txt',
            workspace / 'workspace' / 'clawd_mascot.txt',
            workspace / 'workspace' / 'clawd_config.json',
            workspace / 'workspace' / 'mascot.txt',
            workspace / 'workspace' / 'mascot.json',
        ]
        # Also search for any file with 'mascot' or 'clawd' in the name
        mascot_files = list((workspace / 'workspace').glob('*mascot*')) + list((workspace / 'workspace').glob('*clawd*'))
        output_candidates.extend(mascot_files)
        
        found = None
        for p in output_candidates:
            if p.exists():
                found = p
                break
        passed = found is not None
        detail = f'found {found}' if found else 'no mascot output file found'
    except Exception as e:
        passed = False
        detail = f'error checking output file: {e}'
    checks.append({'name': 'output_exists', 'passed': passed, 'detail': detail})

    # Check 4: if output exists, it should mention blue and arms in a fuzzy way
    try:
        if found is None:
            passed = False
            detail = 'cannot inspect missing output file'
        else:
            text = found.read_text(encoding='utf-8', errors='ignore')
            n = normalize(text)
            
            # Check for blue color - accept both standard blue (34m) and bright blue (94m)
            # Check raw text for ANSI codes since normalize strips escape sequences
            has_blue = (
                'blue' in n or 
                '34m' in text or 
                '94m' in text or
                '\\033[34m' in text or
                '\\033[94m' in text
            )
            
            # Check for arms - look for visual patterns in ASCII art
            # Arms typically appear as vertical bars extending from body (||, | |, etc.)
            has_arms = (
                'arm' in n or 
                'arms' in n or
                '||' in text or  # Common arm pattern in ASCII art
                '| |' in text or
                re.search(r'\|.*\|', text, re.MULTILINE) is not None  # Multiple vertical bars on same line
            )
            
            passed = has_blue and has_arms
            detail = 'mentions blue and arms' if passed else 'output does not clearly mention blue and arms'
    except Exception as e:
        passed = False
        detail = f'error reading output file: {e}'
    checks.append({'name': 'output_mentions_blue_and_arms', 'passed': passed, 'detail': detail})

    score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
    result = {
        'passed': all(c['passed'] for c in checks),
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()