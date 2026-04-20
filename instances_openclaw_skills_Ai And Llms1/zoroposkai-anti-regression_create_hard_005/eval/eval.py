import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


try:
    report_path = workspace / 'output.txt'
    if not report_path.exists():
        add_check('output_exists', False, 'output.txt is missing')
    else:
        text = report_path.read_text(encoding='utf-8', errors='replace')
        norm = re.sub(r'\s+', ' ', text).lower()
        has_title = 'quarterly review' in norm
        has_threshold = '0.87' in norm or '87%' in norm
        has_marker = 'alpha' in norm or 'beta' in norm or 'gamma' in norm
        add_check('report_mentions_quarterly_review', has_title, 'expected phrase not found in output.txt')
        add_check('report_mentions_threshold', has_threshold, 'expected threshold reference not found in output.txt')
        add_check('report_mentions_marker_content', has_marker, 'expected marker-related wording not found in output.txt')
except Exception as e:
    add_check('output_parse', False, f'could not read or parse output.txt: {e}')

try:
    pdf_path = workspace / 'report.pdf'
    if not pdf_path.exists():
        add_check('pdf_exists', False, 'report.pdf is missing')
    else:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(pdf_path))
            num_pages = len(reader.pages)
            extracted = ''
            for page in reader.pages[:3]:
                try:
                    extracted += page.extract_text() or ''
                except Exception:
                    pass
            norm = re.sub(r'\s+', ' ', extracted).lower()
            add_check('pdf_page_count', num_pages >= 1, f'page count={num_pages}')
            add_check('pdf_mentions_quarterly_review', 'quarterly review' in norm, 'text not found in PDF')
        except Exception as e:
            add_check('pdf_readable', False, f'failed to parse PDF: {e}')
except Exception as e:
    add_check('pdf_check', False, f'unexpected error: {e}')

try:
    manifest_path = workspace / 'manifest.json'
    if not manifest_path.exists():
        add_check('manifest_exists', False, 'manifest.json is missing')
    else:
        data = json.loads(manifest_path.read_text(encoding='utf-8', errors='replace'))
        title = str(data.get('title', '')).lower()
        items = data.get('included_incidents', [])
        add_check('manifest_title', 'quarterly review' in title, f'title={data.get("title")!r}')
        add_check('manifest_includes_three_incidents', isinstance(items, list) and len(items) == 3, f'count={len(items) if isinstance(items, list) else "n/a"}')
except Exception as e:
    add_check('manifest_parse', False, f'could not read manifest.json: {e}')

try:
    score = sum(1 for c in checks if c['passed']) / max(len(checks), 1)
    passed = all(c['passed'] for c in checks)
except Exception as e:
    passed = False
    score = 0.0
    add_check('scoring', False, f'failed to compute score: {e}')

print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
