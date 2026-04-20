import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(text):
    return re.sub(r'\s+', ' ', re.sub(r'[\W_]+', ' ', text or '')).strip().lower()


def main():
    checks = []
    workspace = Path(sys.argv[1])

    try:
        out_txt = workspace / 'output.txt'
        if out_txt.exists():
            txt = out_txt.read_text(encoding='utf-8', errors='replace')
            n = normalize(txt)
            checks.append({
                'name': 'output_txt_exists_and_mentions_codename',
                'passed': 'orion r2' in n,
                'detail': 'found codename' if 'orion r2' in n else 'missing codename'
            })
            checks.append({
                'name': 'output_txt_mentions_release_target',
                'passed': '2025 06 15' in n,
                'detail': 'found release target' if '2025 06 15' in n else 'missing release target'
            })
            checks.append({
                'name': 'output_txt_contains_marker_exactly_once',
                'passed': txt.count('[[DOC-MARK-7F3A]]') == 1,
                'detail': f'marker count={txt.count("[[DOC-MARK-7F3A]]")}'
            })
        else:
            checks.extend([
                {'name': 'output_txt_exists_and_mentions_codename', 'passed': False, 'detail': 'output.txt missing'},
                {'name': 'output_txt_mentions_release_target', 'passed': False, 'detail': 'output.txt missing'},
                {'name': 'output_txt_contains_marker_exactly_once', 'passed': False, 'detail': 'output.txt missing'},
            ])
    except Exception as e:
        checks.append({'name': 'output_txt_read', 'passed': False, 'detail': str(e)})

    try:
        out_json = workspace / 'summary.json'
        if out_json.exists():
            try:
                data = json.loads(out_json.read_text(encoding='utf-8', errors='replace'))
                c1 = str(data.get('codename', '')).strip().lower() == 'orion-r2'.lower()
                c2 = str(data.get('release_target', '')).strip() == '2025-06-15'
                actions = data.get('action_items', [])
                c3 = isinstance(actions, list) and len(actions) >= 2
                checks.append({'name': 'summary_json_codename', 'passed': c1, 'detail': f'codename={data.get("codename")!r}'})
                checks.append({'name': 'summary_json_release_target', 'passed': c2, 'detail': f'release_target={data.get("release_target")!r}'})
                checks.append({'name': 'summary_json_actions', 'passed': c3, 'detail': f'action_items={actions!r}'})
            except Exception as e:
                checks.extend([
                    {'name': 'summary_json_codename', 'passed': False, 'detail': f'JSON parse failed: {e}'},
                    {'name': 'summary_json_release_target', 'passed': False, 'detail': 'JSON parse failed'},
                    {'name': 'summary_json_actions', 'passed': False, 'detail': 'JSON parse failed'},
                ])
        else:
            checks.extend([
                {'name': 'summary_json_codename', 'passed': False, 'detail': 'summary.json missing'},
                {'name': 'summary_json_release_target', 'passed': False, 'detail': 'summary.json missing'},
                {'name': 'summary_json_actions', 'passed': False, 'detail': 'summary.json missing'},
            ])
    except Exception as e:
        checks.append({'name': 'summary_json_read', 'passed': False, 'detail': str(e)})

    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks) if checks else 0.0
    result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
