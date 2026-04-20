import json
import os
import re
import sys
from pathlib import Path


def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()
    except Exception:
        return ''


def read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, f'failed to read {path}: {e}'


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    
    # Check for output file - try both possible locations
    out_path = workspace / 'avatar_state.json'
    alt_path = workspace / '.clawface' / 'avatar_state.json'
    
    # Check 1: file exists
    exists = out_path.exists() or alt_path.exists()
    actual_path = out_path if out_path.exists() else alt_path if alt_path.exists() else None
    checks.append({
        'name': 'output file exists',
        'passed': exists,
        'detail': f'found: {actual_path}' if exists else f'missing: {out_path}'
    })

    data = None
    if actual_path and actual_path.exists():
        try:
            data = json.loads(actual_path.read_text(encoding='utf-8'))
            checks.append({'name': 'valid json', 'passed': True, 'detail': 'parsed successfully'})
        except Exception as e:
            checks.append({'name': 'valid json', 'passed': False, 'detail': f'could not parse JSON: {e}'})
    else:
        checks.append({'name': 'valid json', 'passed': False, 'detail': 'file missing'})

    # Load markers
    project_name = None
    marker_ok = False
    try:
        ptxt = (workspace / 'inputs' / 'project_name.txt').read_text(encoding='utf-8', errors='replace')
        project_name = ptxt.strip()
        checks.append({'name': 'project marker present', 'passed': bool(norm(project_name)), 'detail': f'project_name={project_name!r}'})
    except Exception as e:
        checks.append({'name': 'project marker present', 'passed': False, 'detail': f'failed to read project marker: {e}'})
    try:
        notes = json.loads((workspace / 'inputs' / 'notes.json').read_text(encoding='utf-8', errors='replace'))
        marker_ok = str(notes.get('marker', '')).lower() == 'clawface_ok'
        checks.append({'name': 'input marker present', 'passed': marker_ok, 'detail': f"marker={notes.get('marker')!r}"})
    except Exception as e:
        checks.append({'name': 'input marker present', 'passed': False, 'detail': f'failed to read notes.json: {e}'})

    # Content checks on output - flexible key matching
    if isinstance(data, dict):
        # Flexible state/emotion check - accept various key names
        state_value = None
        for key in ['avatar_state', 'emotion', 'state', 'status']:
            if key in data:
                state_value = data[key]
                break
        
        # Check if state indicates success/happiness
        state_str = norm(str(state_value) if state_value else '')
        success_indicators = {'happy', 'excited', 'proud', 'success', 'successful', 'completed', 'done', 'ok'}
        state_passed = any(ind in state_str for ind in success_indicators)
        checks.append({'name': 'emotion is successful', 'passed': state_passed, 'detail': f'state={state_value!r}'})
        
        # Check for completion indicator in any field
        completion_passed = False
        for key, val in data.items():
            val_str = norm(str(val))
            if any(ind in val_str for ind in {'success', 'complete', 'done', 'finished', 'ok'}):
                completion_passed = True
                break
        checks.append({'name': 'action indicates completion', 'passed': completion_passed, 'detail': f'completion indicators found'})
        
        # Check for celebratory effect (emojis or celebratory words)
        effect_passed = False
        for key, val in data.items():
            val_str = str(val)
            if any(ind in val_str.lower() for ind in {'celebrat', 'confetti', 'sparkle', 'smile', '🎉', '✨', '🤖', '🎊'}):
                effect_passed = True
                break
        checks.append({'name': 'effect is celebratory or calm', 'passed': effect_passed, 'detail': f'celebratory indicators found'})
        
        # Message check - flexible key matching
        message = ''
        for key in ['message', 'msg', 'custom_message', 'note', 'summary']:
            if key in data:
                message = str(data[key])
                break
        
        if project_name:
            checks.append({'name': 'message mentions project', 'passed': norm(project_name) in norm(message), 'detail': f'message={message!r}'})
        else:
            checks.append({'name': 'message mentions project', 'passed': False, 'detail': 'project name unavailable'})
        checks.append({'name': 'message is non-empty', 'passed': len(message.strip()) > 0, 'detail': f'len={len(message.strip())}'})
    else:
        for name in ['emotion is successful', 'action indicates completion', 'effect is celebratory or calm', 'message mentions project', 'message is non-empty']:
            checks.append({'name': name, 'passed': False, 'detail': 'no parsed output data'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    passed = passed_count == total

    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()