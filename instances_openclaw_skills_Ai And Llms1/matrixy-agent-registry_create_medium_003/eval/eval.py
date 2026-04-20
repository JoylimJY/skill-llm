from pathlib import Path
import json, re, os, sys

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', str(s).lower())
    except Exception:
        return ''

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

# Check 1: marker file exists and contains marker
try:
    p = workspace / 'notes' / 'README.txt'
    if not p.exists():
        add_check('readme_exists', False, 'notes/README.txt is missing')
    else:
        text = p.read_text(encoding='utf-8', errors='replace')
        passed = 'AR-2025-04-17' in text and 'AGENT-REGISTRY TASK MARKER' in text
        add_check('readme_exists', passed, 'marker found' if passed else 'required marker text missing')
except Exception as e:
    add_check('readme_exists', False, f'error reading README: {e}')

# Check 2: manifest contains expected fields loosely
try:
    p = workspace / 'manifest.json'
    if not p.exists():
        add_check('manifest_valid', False, 'manifest.json is missing')
    else:
        data = json.loads(p.read_text(encoding='utf-8', errors='replace'))
        passed = norm(data.get('project')) == norm('agent-registry') and norm(data.get('marker')) == norm('AR-2025-04-17')
        add_check('manifest_valid', passed, f'project={data.get("project")!r}, marker={data.get("marker")!r}')
except Exception as e:
    add_check('manifest_valid', False, f'error parsing manifest: {e}')

# Check 3: pdf exists and contains marker text somewhere
try:
    p = workspace / 'notes' / 'source.pdf'
    if not p.exists():
        add_check('pdf_contains_marker', False, 'notes/source.pdf is missing')
    else:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(p))
            extracted = '\n'.join((page.extract_text() or '') for page in reader.pages)
            passed = norm('AR-2025-04-17') in norm(extracted) and norm('security-auditor') in norm(extracted)
            add_check('pdf_contains_marker', passed, 'marker and role hint found in pdf text' if passed else 'expected text not found in extracted pdf text')
        except Exception as e:
            add_check('pdf_contains_marker', False, f'error reading pdf: {e}')
except Exception as e:
    add_check('pdf_contains_marker', False, f'error accessing pdf: {e}')

score = (sum(1 for c in checks if c['passed'])) / (len(checks) if checks else 1)
passed = all(c['passed'] for c in checks)
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
