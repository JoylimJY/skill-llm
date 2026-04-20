import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

# Helper functions

def read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, f'could not read {path}: {e}'


def fuzzy_contains(text, needles):
    try:
        t = (text or '').lower()
        return all(n.lower() in t for n in needles)
    except Exception:
        return False

# 1) config.json should exist and retain marker/property compatibility
try:
    config_path = workspace / 'config.json'
    if not config_path.exists():
        add_check('config_exists', False, 'config.json missing')
        config = None
    else:
        try:
            config = json.loads(config_path.read_text(encoding='utf-8'))
            ok = isinstance(config, dict)
            detail = 'loaded' if ok else 'config is not a JSON object'
            add_check('config_exists', ok, detail)
        except Exception as e:
            config = None
            add_check('config_exists', False, f'config.json malformed: {e}')
except Exception as e:
    config = None
    add_check('config_exists', False, f'unexpected error: {e}')

# 2) state.json should exist and be parseable
try:
    state_path = workspace / 'state.json'
    if not state_path.exists():
        add_check('state_exists', False, 'state.json missing')
        state = None
    else:
        try:
            state = json.loads(state_path.read_text(encoding='utf-8'))
            ok = isinstance(state, dict)
            detail = 'loaded' if ok else 'state is not a JSON object'
            add_check('state_exists', ok, detail)
        except Exception as e:
            state = None
            add_check('state_exists', False, f'state.json malformed: {e}')
except Exception as e:
    state = None
    add_check('state_exists', False, f'unexpected error: {e}')

# 3) Display should preserve auto-idle behavior references in source
try:
    src = (workspace / 'scripts' / 'display.py').read_text(encoding='utf-8')
    # Check for idle/timeout handling, state management, and monogram loading
    has_idle = bool(re.search(r'idle|timeout|sleep', src, re.I))
    has_state = bool(re.search(r'state|status', src, re.I))
    has_monogram = bool(re.search(r'monogram|mono|assets.*monograms', src, re.I))
    ok = has_idle and has_state and has_monogram
    add_check('display_preserves_core_behavior', ok, 
              f'idle={has_idle}, state={has_state}, monogram={has_monogram}')
except Exception as e:
    add_check('display_preserves_core_behavior', False, f'could not inspect display.py: {e}')

# 4) Footer/mode hint addition: look for a footer-like render and script name mention
try:
    src = (workspace / 'scripts' / 'display.py').read_text(encoding='utf-8')
    # Check for footer rendering, script name, or mode display
    has_footer = bool(re.search(r'footer|bottom|script.*name|mode.*hint', src, re.I))
    has_display_ref = bool(re.search(r'display|status|configure', src, re.I))
    ok = has_footer and has_display_ref
    add_check('display_footer_added', ok, f'footer={has_footer}, display_ref={has_display_ref}')
except Exception as e:
    add_check('display_footer_added', False, f'could not inspect display.py: {e}')

# 5) configure should be safe on fresh checkout and not clobber existing config markers
try:
    src = (workspace / 'scripts' / 'configure.py').read_text(encoding='utf-8')
    # Check for config loading, saving, and existence checking
    has_load = bool(re.search(r'load|read|open.*config|json.*load', src, re.I))
    has_save = bool(re.search(r'save|write|dump|json.*dump', src, re.I))
    has_check = bool(re.search(r'exist|check|force|overwrite|already', src, re.I))
    ok = has_load and has_save and has_check
    add_check('configure_safe_init_support', ok, 
              f'load={has_load}, save={has_save}, check={has_check}')
except Exception as e:
    add_check('configure_safe_init_support', False, f'could not inspect configure.py: {e}')

# 6) Monogram preference: if a custom monogram exists, the code should reference assets/monograms and use the configured letter
try:
    src = (workspace / 'scripts' / 'display.py').read_text(encoding='utf-8')
    # Check for monogram path, letter lookup, and fallback logic
    has_path = bool(re.search(r'assets.*monograms|monograms.*assets', src, re.I))
    has_letter = bool(re.search(r'letter|config.*letter', src, re.I))
    has_fallback = bool(re.search(r'fallback|default|if.*exist|try.*except|or.*default', src, re.I))
    ok = has_path and has_letter and has_fallback
    add_check('custom_monogram_preference', ok, 
              f'path={has_path}, letter={has_letter}, fallback={has_fallback}')
except Exception as e:
    add_check('custom_monogram_preference', False, f'could not inspect display.py: {e}')

# 7) Verify generated marker files remain present (objective file checks)
try:
    marker_file = workspace / 'assets' / 'monograms' / 'M.txt'
    if not marker_file.exists():
        add_check('marker_monogram_present', False, 'assets/monograms/M.txt missing')
    else:
        try:
            txt = marker_file.read_text(encoding='utf-8')
            ok = 'MARKER-MONO-M-TOP' in txt and 'MARKER-MONO-M-BOTTOM' in txt
            add_check('marker_monogram_present', ok, 'marker lines verified' if ok else 'marker lines missing')
        except Exception as e:
            add_check('marker_monogram_present', False, f'could not read marker monogram: {e}')
except Exception as e:
    add_check('marker_monogram_present', False, f'unexpected error: {e}')

# Score
passed_count = sum(1 for c in checks if c['passed'])
total = len(checks) if checks else 1
score = passed_count / total
passed = passed_count == total

result = {'passed': passed, 'score': score, 'checks': checks}
print(json.dumps(result, indent=2))