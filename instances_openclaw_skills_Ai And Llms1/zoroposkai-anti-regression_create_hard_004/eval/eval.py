import json
import os
import re
from pathlib import Path

workspace = Path(os.sys.argv[1]) if len(os.sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

def safe_read(path):
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)

# Check 1: SUMMARY.md exists and has required sections
try:
    p = workspace / 'SUMMARY.md'
    if not p.exists():
        add_check('summary_exists', False, 'SUMMARY.md is missing')
    else:
        text = p.read_text(encoding='utf-8', errors='replace')
        norm = re.sub(r'\s+', ' ', text).lower()
        ok = all(s.lower() in norm for s in ['overview', 'key files', 'notes'])
        add_check('summary_sections', ok, 'Found required sections' if ok else 'Missing one or more required sections')
except Exception as e:
    add_check('summary_sections', False, f'Error reading SUMMARY.md: {e}')

# Check 2: deliverable files exist
for fname in ['deliverable/README.md', 'deliverable/CHANGELOG.md', 'deliverable/notes.json']:
    try:
        p = workspace / fname
        add_check(f'{fname}_exists', p.exists(), 'exists' if p.exists() else 'missing')
    except Exception as e:
        add_check(f'{fname}_exists', False, f'Error checking existence: {e}')

# Check 3: README content
try:
    p = workspace / 'deliverable' / 'README.md'
    if not p.exists():
        add_check('readme_content', False, 'README.md missing')
    else:
        text = p.read_text(encoding='utf-8', errors='replace')
        lower = text.lower()
        has_desc = 'orion toolkit' in lower or 'project' in lower
        has_list = bool(re.search(r'(?m)^\s*1\s*[\.).-]\s+', text))
        has_code = '```' in text and ('python run_orion.py' in lower or '--help' in lower)
        ok = has_desc and has_list and has_code
        add_check('readme_content', ok, f'desc={has_desc}, list={has_list}, codeblock={has_code}')
except Exception as e:
    add_check('readme_content', False, f'Error reading README.md: {e}')

# Check 4: CHANGELOG has 3 version entries in descending order
try:
    p = workspace / 'deliverable' / 'CHANGELOG.md'
    if not p.exists():
        add_check('changelog_versions', False, 'CHANGELOG.md missing')
    else:
        text = p.read_text(encoding='utf-8', errors='replace')
        versions = re.findall(r'v?(\d+\.\d+\.\d+)', text, flags=re.I)
        ok_count = len(versions) >= 3
        # compare first 3 semver-like versions if available
        def to_tuple(v):
            try:
                return tuple(int(x) for x in v.split('.')[:3])
            except Exception:
                return (0, 0, 0)
        descending = True
        if len(versions) >= 3:
            vals = [to_tuple(v) for v in versions[:3]]
            descending = vals[0] > vals[1] > vals[2]
        ok = ok_count and descending
        add_check('changelog_versions', ok, f'found={versions[:3]}, descending={descending}')
except Exception as e:
    add_check('changelog_versions', False, f'Error reading CHANGELOG.md: {e}')

# Check 5: notes.json valid and includes markers
try:
    p = workspace / 'deliverable' / 'notes.json'
    if not p.exists():
        add_check('notes_json', False, 'notes.json missing')
    else:
        try:
            data = json.loads(p.read_text(encoding='utf-8', errors='replace'))
            markers = ['ORION-47', 'IDX-9031', 'META-5520', 'PDF-1188', 'OUT-7712']
            blob = json.dumps(data).lower()
            ok = all(m.lower() in blob for m in markers)
            add_check('notes_json', ok, 'markers present' if ok else 'missing one or more markers')
        except Exception as e:
            add_check('notes_json', False, f'Invalid JSON or marker check failed: {e}')
except Exception as e:
    add_check('notes_json', False, f'Error checking notes.json: {e}')

# Check 6: input files unchanged/available
try:
    expected_inputs = [
        workspace / 'source' / 'project_brief.txt',
        workspace / 'source' / 'file_index.txt',
        workspace / 'source' / 'metadata.json',
        workspace / 'source' / 'spec.pdf',
        workspace / 'source' / 'sample_output.txt',
    ]
    ok = all(p.exists() for p in expected_inputs)
    add_check('inputs_exist', ok, 'all source files present' if ok else 'one or more source files missing')
except Exception as e:
    add_check('inputs_exist', False, f'Error checking inputs: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
