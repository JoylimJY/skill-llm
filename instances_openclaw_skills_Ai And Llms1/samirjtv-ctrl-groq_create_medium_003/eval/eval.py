import json
import os
import csv
from pathlib import Path

workspace = Path(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    summary_path = workspace / 'summary.txt'
    meta_path = workspace / 'summary_meta.json'
    add_check('summary_exists', summary_path.exists(), 'summary.txt found' if summary_path.exists() else 'summary.txt is missing')
    add_check('meta_exists', meta_path.exists(), 'summary_meta.json found' if meta_path.exists() else 'summary_meta.json is missing')

    source_files = sorted([p.name for p in workspace.glob('input_*.csv')])
    total_rows = 0
    team_counts = {}
    status_counts = {}
    top = None

    for fname in source_files:
        try:
            with open(workspace / fname, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_rows += 1
                    team = (row.get('team') or '').strip()
                    status = (row.get('status') or '').strip()
                    rid = (row.get('id') or '').strip()
                    try:
                        score = float(row.get('score') or 0)
                    except Exception:
                        score = 0.0
                    team_counts[team] = team_counts.get(team, 0) + 1
                    status_counts[status] = status_counts.get(status, 0) + 1
                    candidate = (score, rid, team)
                    if top is None or candidate[0] > top[0] or (candidate[0] == top[0] and candidate[1] < top[1]):
                        top = candidate
        except Exception as e:
            add_check(f'read_{fname}', False, f'Could not read {fname}: {e}')
    if source_files:
        add_check('input_files_present', True, f'Found {len(source_files)} input files')
    else:
        add_check('input_files_present', False, 'No input_*.csv files found')

    expected_team_lines = [f'{k}: {v}' for k, v in sorted(team_counts.items(), key=lambda kv: (-kv[1], kv[0].lower(), kv[0]))]
    expected_status_lines = [f'{k}: {v}' for k, v in sorted(status_counts.items(), key=lambda kv: kv[0].lower())]
    expected_top_line = ''
    if top is not None:
        expected_top_line = f'id={top[1]}, team={top[2]}, score={int(top[0]) if float(top[0]).is_integer() else top[0]}'

    try:
        text = summary_path.read_text(encoding='utf-8') if summary_path.exists() else ''
        norm = ' '.join(text.split()).lower()
        has_team = 'team counts' in norm
        has_status = 'status counts' in norm
        has_top = 'top score' in norm
        add_check('headings_present', has_team and has_status and has_top, 'Required headings found' if (has_team and has_status and has_top) else 'Missing one or more required headings')

        for line in expected_team_lines:
            ok = line.lower() in norm
            add_check(f'team_line_{line}', ok, f'Expected team summary line: {line}' if ok else f'Missing team summary line: {line}')
        for line in expected_status_lines:
            ok = line.lower() in norm
            add_check(f'status_line_{line}', ok, f'Expected status summary line: {line}' if ok else f'Missing status summary line: {line}')
        ok_top = expected_top_line.lower() in norm if expected_top_line else False
        add_check('top_score_line', ok_top, f'Expected top score line: {expected_top_line}' if ok_top else f'Missing or incorrect top score line: {expected_top_line}')
    except Exception as e:
        add_check('summary_parse', False, f'Could not read/parse summary.txt: {e}')

    try:
        meta = json.loads(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
        ok_keys = all(k in meta for k in ['source_files','row_count','top_id','top_team','top_score'])
        add_check('meta_keys', ok_keys, 'All required metadata keys present' if ok_keys else 'Missing one or more metadata keys')
        if ok_keys:
            add_check('meta_source_files', meta.get('source_files') == source_files, f'Expected source_files {source_files}' if meta.get('source_files') == source_files else f'Incorrect source_files: {meta.get("source_files")}')
            add_check('meta_row_count', meta.get('row_count') == total_rows, f'Expected row_count {total_rows}' if meta.get('row_count') == total_rows else f'Incorrect row_count: {meta.get("row_count")}')
            if top is not None:
                add_check('meta_top_id', str(meta.get('top_id')) == str(top[1]), f'Expected top_id {top[1]}' if str(meta.get('top_id')) == str(top[1]) else f'Incorrect top_id: {meta.get("top_id")}')
                add_check('meta_top_team', str(meta.get('top_team')) == str(top[2]), f'Expected top_team {top[2]}' if str(meta.get('top_team')) == str(top[2]) else f'Incorrect top_team: {meta.get("top_team")}')
                try:
                    meta_score = float(meta.get('top_score'))
                except Exception:
                    meta_score = None
                add_check('meta_top_score', meta_score == float(top[0]), f'Expected top_score {top[0]}' if meta_score == float(top[0]) else f'Incorrect top_score: {meta.get("top_score")}')
    except Exception as e:
        add_check('meta_parse', False, f'Could not read/parse summary_meta.json: {e}')

except Exception as e:
    add_check('fatal', False, f'Unexpected evaluator error: {e}')

passed = all(c['passed'] for c in checks) if checks else False
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
