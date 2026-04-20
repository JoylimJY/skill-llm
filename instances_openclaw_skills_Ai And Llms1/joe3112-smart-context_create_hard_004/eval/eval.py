import json
import os
import re
import sys
from pathlib import Path

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

try:
    out = workspace / 'smart_context_playbook.md'
    if not out.exists():
        add_check('output_exists', False, 'smart_context_playbook.md is missing')
    else:
        text = out.read_text(encoding='utf-8', errors='replace')
        norm = re.sub(r'\s+', ' ', text).lower()
        has_exec = 'executive summary' in norm
        has_table = 'decision table' in norm or 'when to read files' in norm
        has_anti = 'anti-pattern' in norm
        has_checklist = 'checklist' in norm or 'tool-call efficiency' in norm
        add_check('required_sections', has_exec and has_table and has_anti and has_checklist,
                  'Found sections: exec=%s table=%s anti=%s checklist=%s' % (has_exec, has_table, has_anti, has_checklist))
        word_count = len(re.findall(r"\b\w+\b", text))
        add_check('word_limit', word_count <= 220, f'Word count is {word_count}, limit is 220')
        bullet_count = len(re.findall(r'(?m)^\s*[-*+]\s+', text))
        add_check('bullet_count', bullet_count >= 8, f'Found {bullet_count} bullets, expected at least 8 total')
        table_like = ('|' in text) and (re.search(r'\|\s*when', norm) or re.search(r'\|\s*answer', norm))
        add_check('table_like_structure', table_like, 'Table structure detected' if table_like else 'No clear decision table structure found')
except Exception as e:
    add_check('output_read_error', False, f'Error reading output: {e}')

try:
    notes = workspace / 'notes.txt'
    if not notes.exists():
        add_check('notes_marker', False, 'notes.txt is missing')
    else:
        t = notes.read_text(encoding='utf-8', errors='replace').lower()
        markers = ['marker alpha', 'marker beta', 'marker gamma']
        ok = all(m in t for m in markers)
        add_check('notes_marker', ok, 'Marker presence in notes.txt: ' + ', '.join(f'{m}={m in t}' for m in markers))
except Exception as e:
    add_check('notes_marker_error', False, f'Error reading notes: {e}')

try:
    pdf = workspace / 'reference.pdf'
    if not pdf.exists():
        add_check('pdf_marker', False, 'reference.pdf is missing')
    else:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(pdf))
            extracted = ' '.join((page.extract_text() or '') for page in reader.pages).lower()
            ok = all(m in extracted for m in ['marker delta', 'marker epsilon'])
            add_check('pdf_marker', ok, 'PDF marker extraction succeeded' if ok else 'Expected markers not found in extracted PDF text')
        except Exception as e:
            add_check('pdf_marker', False, f'PDF parsing error: {e}')
except Exception as e:
    add_check('pdf_marker_error', False, f'Error checking PDF: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
passed = all(c['passed'] for c in checks) if checks else False
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
