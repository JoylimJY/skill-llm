import json
import os
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        text = str(text)
    except Exception:
        return ''
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '', text)
    return text


def read_text(path):
    try:
        content = Path(path).read_text(encoding='utf-8', errors='replace')
        return content, None
    except Exception as e:
        return None, str(e)


def read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

    try:
        marker_path = workspace / 'task_marker.txt'
        if marker_path.exists():
            txt, err = read_text(marker_path)
            # Normalize removes hyphens, so check for normalized versions
            norm = normalize(txt or '')
            ok = (txt is not None and 
                  'clawdpresencedemomarker' in norm and 
                  'expectedlettern' in norm and 
                  'expectednamenova' in norm)
            add_check('marker_file', ok, 'marker present' if ok else f'missing or invalid: {err}')
        else:
            add_check('marker_file', False, 'task_marker.txt is missing')
    except Exception as e:
        add_check('marker_file', False, f'error: {e}')

    try:
        # Check for config.json, presence_config.json, or clawd_config.json
        config_path = None
        for possible_name in ['config.json', 'presence_config.json', 'clawd_config.json']:
            p = workspace / possible_name
            if p.exists():
                config_path = p
                break
        
        if config_path:
            data, err = read_json(config_path)
            if isinstance(data, dict):
                letter = normalize(data.get('letter', ''))
                name = normalize(data.get('name', ''))
                timeout = data.get('idle_timeout', None)
                ok = (letter == 'n' or 'n' in letter[:1]) and ('nova' in name) and (isinstance(timeout, int) and 700 <= timeout <= 750)
                detail = f"letter={data.get('letter')}, name={data.get('name')}, idle_timeout={timeout}"
                add_check('config_values', ok, detail)
            else:
                add_check('config_values', False, f'config invalid: {err}')
        else:
            add_check('config_values', False, 'config.json, presence_config.json, or clawd_config.json is missing')
    except Exception as e:
        add_check('config_values', False, f'error: {e}')

    try:
        # Check for state.json or presence_status.json
        state_path = None
        for possible_name in ['state.json', 'presence_status.json']:
            p = workspace / possible_name
            if p.exists():
                state_path = p
                break
        
        if state_path:
            data, err = read_json(state_path)
            if isinstance(data, dict):
                state = normalize(data.get('state', ''))
                msg = normalize(data.get('message', ''))
                # Accept either 'updated' (numeric) or 'last_transition' (string)
                updated = data.get('updated', None)
                last_transition = data.get('last_transition', None)
                has_timestamp = (isinstance(updated, (int, float)) or 
                                (isinstance(last_transition, str) and len(last_transition) > 0))
                ok = state in {'idle', 'sleep'} and msg == '' and has_timestamp
                detail = f"state={data.get('state')}, message={data.get('message')}, updated_type={type(updated).__name__ if updated else 'None'}, last_transition={last_transition}"
                add_check('final_state', ok, detail)
            else:
                add_check('final_state', False, f'state invalid: {err}')
        else:
            add_check('final_state', False, 'state.json or presence_status.json is missing')
    except Exception as e:
        add_check('final_state', False, f'error: {e}')

    try:
        mono_path = workspace / 'assets' / 'monograms' / 'N.txt'
        if mono_path.exists():
            txt, err = read_text(mono_path)
            # Normalize removes colons and hyphens, so check for normalized version
            norm = normalize(txt or '')
            ok = (txt is not None and 
                  'markernovan' in norm and 
                  ('n   n' in txt.lower() or 'n    n' in txt.lower()))
            add_check('custom_monogram', ok, 'custom N monogram found' if ok else f'content issue: {err}')
        else:
            add_check('custom_monogram', False, 'assets/monograms/N.txt is missing')
    except Exception as e:
        add_check('custom_monogram', False, f'error: {e}')

    try:
        # Check for presence_plan.txt or state_transitions_applied.txt
        note_path = None
        for possible_name in ['presence_plan.txt', 'state_transitions_applied.txt']:
            p = workspace / possible_name
            if p.exists():
                note_path = p
                break
        
        if note_path:
            txt, err = read_text(note_path)
            norm = normalize(txt or '')
            expected_fragments = ['idlework', 'workthink', 'thinkalert', 'alertidle', 'finaltargetidlewithmessagecleared']
            ok = txt is not None and all(fragment in norm for fragment in expected_fragments)
            add_check('transition_note', ok, 'transition plan content verified' if ok else f'content issue: {err}')
        else:
            add_check('transition_note', False, 'presence_plan.txt or state_transitions_applied.txt is missing')
    except Exception as e:
        add_check('transition_note', False, f'error: {e}')

    total = len(checks) if checks else 1
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total
    passed = passed_count == total
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': 'unexpected evaluator failure'}]}, ensure_ascii=False))