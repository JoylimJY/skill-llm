import json
import os
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def safe_load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return ''.join(ch.lower() for ch in str(s) if ch.isalnum())
    except Exception:
        return ''


def main():
    import sys
    ws = Path(sys.argv[1])
    checks = []

    def add(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

    try:
        out_jsonl = ws / 'output.jsonl'
        report_json = ws / 'report.json'
        readme_txt = ws / 'README.txt'

        if out_jsonl.exists():
            content = safe_read_text(out_jsonl)
            if isinstance(content, tuple):
                _, err = content
                add('output_jsonl_readable', False, err)
                rows = []
            else:
                text = content
                rows = []
                try:
                    for line in text.splitlines():
                        if line.strip():
                            rows.append(json.loads(line))
                    add('output_jsonl_exists_and_parseable', len(rows) > 0, f'parsed {len(rows)} records')
                except Exception as e:
                    add('output_jsonl_exists_and_parseable', False, f'parse error: {e}')
        else:
            add('output_jsonl_exists_and_parseable', False, 'output.jsonl missing')
            rows = []

        if report_json.exists():
            report, err = safe_load_json(report_json)
            if err:
                add('report_json_parseable', False, err)
            else:
                add('report_json_parseable', True, 'report.json parsed')
                if isinstance(report, dict):
                    add('report_has_required_keys', all(k in report for k in ['total_jobs', 'valid_jobs', 'invalid_jobs']), f"keys={list(report.keys())}")
                else:
                    add('report_has_required_keys', False, 'report is not an object')
        else:
            add('report_json_parseable', False, 'report.json missing')
            add('report_has_required_keys', False, 'report.json missing')
            report = None

        if readme_txt.exists():
            txt, err = safe_read_text(readme_txt)
            if err:
                add('readme_written', False, err)
            else:
                norm = normalize(txt)
                add('readme_written', 'groq' in norm and 'jsonl' in norm, 'README text present')
        else:
            add('readme_written', False, 'README.txt missing')

        # Content checks against inputs in workspace root
        template_path = ws / 'template.json'
        jobs_path = ws / 'jobs.jsonl'
        marker_path = ws / 'marker.txt'

        template, terr = safe_load_json(template_path)
        jobs_text, jerr = safe_read_text(jobs_path)
        marker, merr = safe_read_text(marker_path)

        if isinstance(template, tuple):
            add('template_available', False, terr)
        else:
            add('template_available', True, 'template loaded')

        if isinstance(jobs_text, tuple):
            add('jobs_available', False, jerr)
        else:
            add('jobs_available', True, 'jobs loaded')

        if isinstance(marker, tuple):
            add('marker_available', False, merr)
        else:
            add('marker_available', True, 'marker loaded')

        if rows:
            # Flexible content validation
            job_ids = {r.get('job_id') for r in rows if isinstance(r, dict)}
            add('contains_all_jobs', {'alpha-001', 'beta-002', 'gamma-003'}.issubset(job_ids), f'job_ids={sorted([j for j in job_ids if j])}')
            markers_present = any('groq-marker-beta' in normalize(v.get('content', '')) for r in rows if isinstance(r, dict) for v in r.get('messages', []) if isinstance(v, dict))
            markers_present = markers_present or any('gamma-seed-7788' in normalize(v.get('content', '')) for r in rows if isinstance(r, dict) for v in r.get('messages', []) if isinstance(v, dict))
            add('marker_content_preserved', markers_present, 'marker strings found in output')
            whitespace_trimmed = any(any(isinstance(v, dict) and v.get('content', '') == 'first request' for v in r.get('messages', [])) for r in rows if isinstance(r, dict))
            add('message_whitespace_normalized', whitespace_trimmed, 'whitespace normalization observed')

        total = len(checks)
        passed = sum(1 for c in checks if c['passed'])
        score = (passed / total) if total else 0.0
        result = {'passed': passed == total and total > 0, 'score': score, 'checks': checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        result = {'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': str(e)}]}
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
