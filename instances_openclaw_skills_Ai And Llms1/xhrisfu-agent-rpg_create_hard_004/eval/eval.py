import json
import os
import re
import sys
from pathlib import Path

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    ws = Path(sys.argv[1])
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argument", "passed": False, "detail": f"Invalid workspace argument: {e}"}]}))
    sys.exit(0)

# Check 1: expected output exists
try:
    output_path = ws / 'output.txt'
    exists = output_path.exists()
    add_check('output_exists', exists, 'output.txt found' if exists else 'output.txt is missing')
except Exception as e:
    add_check('output_exists', False, f'Error checking output existence: {e}')

# Check 2: output contains an English JSON-like task artifact marker
try:
    text = output_path.read_text(encoding='utf-8', errors='replace') if output_path.exists() else ''
    norm = re.sub(r'\s+', ' ', text.lower())
    ok = ('agent-rpg' in norm) and ('json' in norm) and ('eval_script' in norm)
    add_check('content_markers', ok, 'Found required markers' if ok else 'Missing required markers in output')
except Exception as e:
    add_check('content_markers', False, f'Error reading output: {e}')

# Check 3: deterministic marker inputs exist and contain markers
try:
    campaign = ws / 'inputs' / 'campaign_brief.txt'
    ok = False
    detail = 'campaign_brief.txt missing'
    if campaign.exists():
        txt = campaign.read_text(encoding='utf-8', errors='replace')
        ok = 'marker_campaign_brief' in txt.lower() and 'chrome veil' in txt.lower() and 'ash choir' in txt.lower()
        detail = 'campaign marker content verified' if ok else 'campaign marker content mismatch'
    add_check('seed_marker_file', ok, detail)
except Exception as e:
    add_check('seed_marker_file', False, f'Error verifying marker file: {e}')

# Check 4: PDF exists and contains marker text loosely
try:
    pdf_path = ws / 'inputs' / 'briefing.pdf'
    ok = False
    detail = 'briefing.pdf missing'
    if pdf_path.exists():
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))
            full = ''
            for page in reader.pages:
                try:
                    full += page.extract_text() or ''
                except Exception:
                    pass
            low = full.lower()
            ok = 'marker_map_page_1' in low and 'missing courier' in low and 'pact ledger' in low
            detail = 'PDF text markers verified' if ok else 'PDF content markers not found'
        except Exception as e:
            detail = f'PDF parse failed: {e}'
    add_check('pdf_marker_content', ok, detail)
except Exception as e:
    add_check('pdf_marker_content', False, f'Error verifying PDF: {e}')

# Check 5: json seed data valid and deterministic
try:
    seed_path = ws / 'inputs' / 'seed_data.json'
    ok = False
    detail = 'seed_data.json missing'
    if seed_path.exists():
        data = json.loads(seed_path.read_text(encoding='utf-8', errors='replace'))
        ok = data.get('seed') == 1337 and data.get('campaign_name') and 'required_markers' in data
        detail = 'Seed data verified' if ok else 'Seed data content mismatch'
    add_check('seed_data', ok, detail)
except Exception as e:
    add_check('seed_data', False, f'Error verifying seed data: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
passed = passed_count == len(checks)
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))