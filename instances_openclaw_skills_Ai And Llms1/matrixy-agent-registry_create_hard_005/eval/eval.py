import json
import os
import re
import sys
from pathlib import Path


def norm(text):
    try:
        return re.sub(r'[^a-z0-9]+', '', text.lower())
    except Exception:
        return ''


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        readme_path = workspace / 'README.md'
        if readme_path.exists():
            txt, err = safe_read(readme_path)
            if txt is not None:
                n = norm(txt)
                passed = ('lazy' in n or 'searchfirst' in n) and ('donotpreload' in n or 'preloadallagents' in n)
                add_check('readme_mentions_lazy_loading', passed, 'README contains lazy-loading guidance and preload restriction' if passed else 'README missing required guidance')
            else:
                add_check('readme_mentions_lazy_loading', False, f'Could not read README: {err}')
        else:
            add_check('readme_mentions_lazy_loading', False, 'README.md is missing')
    except Exception as e:
        add_check('readme_mentions_lazy_loading', False, f'Unexpected error: {e}')

    try:
        marker_path = workspace / 'registry' / 'marker.json'
        if marker_path.exists():
            txt, err = safe_read(marker_path)
            if txt is not None:
                try:
                    data = json.loads(txt)
                    marker_ok = norm(data.get('marker_id', '')) == norm('REGISTRY_MARKER_48271')
                    hint_ok = 'search first' in norm(data.get('hint', '')) or 'load on demand' in norm(data.get('hint', ''))
                    add_check('registry_marker_present', marker_ok and hint_ok, 'Registry marker matches expected content' if marker_ok and hint_ok else 'Registry marker content mismatch')
                except Exception as e:
                    add_check('registry_marker_present', False, f'Invalid JSON in marker file: {e}')
            else:
                add_check('registry_marker_present', False, f'Could not read marker file: {err}')
        else:
            add_check('registry_marker_present', False, 'registry/marker.json is missing')
    except Exception as e:
        add_check('registry_marker_present', False, f'Unexpected error: {e}')

    try:
        agents_dir = workspace / 'agents'
        required = ['security-auditor.json', 'code-reviewer.json', 'docs-curator.json']
        if agents_dir.exists():
            found = []
            for fname in required:
                p = agents_dir / fname
                if p.exists():
                    txt, err = safe_read(p)
                    if txt is not None:
                        try:
                            data = json.loads(txt)
                            name = norm(data.get('name', ''))
                            desc = norm(data.get('description', ''))
                            instr = norm(data.get('instructions', ''))
                            ok = len(name) > 0 and len(desc) > 0 and len(instr) > 0
                            if 'security' in fname:
                                ok = ok and ('security' in desc or 'security' in instr)
                            if 'code-reviewer' in fname:
                                ok = ok and ('review' in desc or 'review' in instr)
                            if 'docs-curator' in fname:
                                ok = ok and ('doc' in desc or 'doc' in instr)
                            found.append(ok)
                        except Exception as e:
                            found.append(False)
                    else:
                        found.append(False)
                else:
                    found.append(False)
            passed = all(found)
            add_check('sample_agents_exist', passed, 'All expected agent files exist with plausible content' if passed else 'One or more agent files are missing or malformed')
        else:
            add_check('sample_agents_exist', False, 'agents directory is missing')
    except Exception as e:
        add_check('sample_agents_exist', False, f'Unexpected error: {e}')

    try:
        total = len(checks)
        passed_count = sum(1 for c in checks if c['passed'])
        score = passed_count / total if total else 0.0
        passed = passed_count == total and total > 0
        result = {'passed': passed, 'score': score, 'checks': checks}
        print(json.dumps(result))
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks if 'checks' in locals() else []}))


if __name__ == '__main__':
    main()
