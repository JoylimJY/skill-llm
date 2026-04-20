import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def fuzzy_contains(text, needle):
    try:
        if text is None:
            return False
        t = re.sub(r'\s+', ' ', text.lower())
        n = re.sub(r'\s+', ' ', needle.lower())
        return n in t
    except Exception:
        return False


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    # 1) Required files exist
    required = [
        'guard.js',
        'status_snapshot.txt',
        'status_snapshot_alt.txt',
        'model_targets.json',
        'quota_report.pdf',
    ]
    missing = []
    for fname in required:
        try:
            if not (workspace / fname).exists():
                missing.append(fname)
        except Exception as e:
            missing.append(f'{fname} (error: {e})')
    add_check('required_files_exist', len(missing) == 0, 'Missing: ' + (', '.join(missing) if missing else 'none'))

    # 2) Marker content in text file
    try:
        txt, err = safe_read_text(workspace / 'status_snapshot.txt')
        if isinstance(txt, tuple):
            txt, err = txt
        passed = fuzzy_contains(txt, 'MARKER_STATUS_ALPHA_9b7e') and fuzzy_contains(txt, '78% left')
        add_check('status_snapshot_marker', passed, 'Marker and quota text ' + ('found' if passed else 'not found') + ('' if not err else f'; read_error={err}'))
    except Exception as e:
        add_check('status_snapshot_marker', False, f'Exception: {e}')

    # 3) Alternative snapshot has low quota markers
    try:
        txt, err = safe_read_text(workspace / 'status_snapshot_alt.txt')
        if isinstance(txt, tuple):
            txt, err = txt
        passed = fuzzy_contains(txt, 'MARKER_STATUS_BETA_2c4d') and fuzzy_contains(txt, '12% left') and fuzzy_contains(txt, '19% left')
        add_check('status_snapshot_alt_marker', passed, 'Low-quota markers ' + ('found' if passed else 'not found') + ('' if not err else f'; read_error={err}'))
    except Exception as e:
        add_check('status_snapshot_alt_marker', False, f'Exception: {e}')

    # 4) JSON contains expected keys and marker
    try:
        raw, err = safe_read_text(workspace / 'model_targets.json')
        if isinstance(raw, tuple):
            raw, err = raw
        obj = json.loads(raw) if raw else {}
        passed = all(k in obj for k in ['preferred', 'fallback', 'threshold', 'marker']) and str(obj.get('threshold')) == '20' and fuzzy_contains(raw, 'MARKER_JSON_44aa')
        add_check('model_targets_json', passed, 'JSON structure ' + ('valid' if passed else 'invalid') + ('' if not err else f'; read_error={err}'))
    except Exception as e:
        add_check('model_targets_json', False, f'Exception: {e}')

    # 5) PDF contains marker text and at least 2 pages
    try:
        passed = False
        detail = 'unknown'
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(workspace / 'quota_report.pdf'))
            pages = len(reader.pages)
            text = ''
            try:
                for p in reader.pages:
                    try:
                        text += (p.extract_text() or '') + '\n'
                    except Exception:
                        pass
            except Exception as e:
                detail = f'page_iteration_error={e}'
            passed = pages >= 2 and fuzzy_contains(text, 'MARKER_PDF_DELTA_77ff') and fuzzy_contains(text, 'claude-sonnet-4-5-thinking 33% left')
            detail = f'pages={pages}; marker_found={fuzzy_contains(text, "MARKER_PDF_DELTA_77ff")}; appendix_text_found={fuzzy_contains(text, "claude-sonnet-4-5-thinking 33% left")}'
        except Exception as e:
            detail = f'pdf_read_error={e}'
        add_check('pdf_marker_and_pages', passed, detail)
    except Exception as e:
        add_check('pdf_marker_and_pages', False, f'Exception: {e}')

    # score
    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = (passed_count / total) if total else 0.0
    result = {
        'passed': passed_count == total,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': f'Unexpected error: {e}'}]}))
