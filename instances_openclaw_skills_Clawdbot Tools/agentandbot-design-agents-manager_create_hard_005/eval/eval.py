import json
import os
from pathlib import Path

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

workspace = Path(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

# 1. Required output files exist (PDF is optional - other files are critical)
required_files = ['registry_report.md', 'routing_audit.json']
optional_files = ['hierarchy.pdf']

for fname in required_files:
    try:
        exists = (workspace / fname).exists()
        add_check(f'file_exists::{fname}', exists, 'found' if exists else 'missing')
    except Exception as e:
        add_check(f'file_exists::{fname}', False, f'error checking existence: {e}')

# PDF is optional - check if it exists but don't fail if missing
for fname in optional_files:
    try:
        exists = (workspace / fname).exists()
        add_check(f'file_exists::{fname}', exists, 'found' if exists else 'optional - not required')
    except Exception as e:
        add_check(f'file_exists::{fname}', False, f'error checking existence: {e}')

# 2. Report mentions core routing facts with fuzzy matching
try:
    text = (workspace / 'registry_report.md').read_text(encoding='utf-8', errors='ignore') if (workspace / 'registry_report.md').exists() else ''
    t = ' '.join(text.lower().split())
    ok = all(k in t for k in ['main', 'ilkerkaan', 'research-1', 'dev-1', 'ops-1']) and ('can assign' in t or 'can_assign_to' in t)
    add_check('report_content', ok, 'contains expected agent names and routing language' if ok else 'missing one or more expected routing terms')
except Exception as e:
    add_check('report_content', False, f'error reading report: {e}')

# 3. JSON audit is parseable and contains approval/handshake mention
try:
    raw = (workspace / 'routing_audit.json').read_text(encoding='utf-8', errors='ignore') if (workspace / 'routing_audit.json').exists() else ''
    data = json.loads(raw)
    audit_text = json.dumps(data, ensure_ascii=False).lower()
    ok = isinstance(data, dict) and any(k in audit_text for k in ['handshake', 'approval'])
    add_check('audit_json', ok, 'parseable JSON with approval/handshake mention' if ok else 'JSON missing handshake/approval text')
except Exception as e:
    add_check('audit_json', False, f'error parsing audit json: {e}')

# 4. PDF contains routing names (optional check - only validates if PDF exists)
try:
    pdf_ok = False
    detail = 'pdf not provided (optional)'
    pdf_path = workspace / 'hierarchy.pdf'
    
    # Read the marker from seed file if available
    expected_marker = None
    seed_path = workspace / 'registry_seed.json'
    if seed_path.exists():
        try:
            with open(seed_path, 'r') as f:
                seed_data = json.load(f)
                expected_marker = seed_data.get('marker', '').lower()
        except Exception:
            pass
    
    if pdf_path.exists() and PyPDF2 is not None:
        try:
            reader = PyPDF2.PdfReader(str(pdf_path))
            extracted = []
            for page in reader.pages[:5]:
                try:
                    extracted.append(page.extract_text() or '')
                except Exception:
                    extracted.append('')
            txt = ' '.join(extracted).lower()
            
            # Check for routing names (required)
            has_routing_names = 'ilkerkaan' in txt and 'main' in txt
            
            # Check for marker (flexible - accept seed marker or any marker-like string)
            has_marker = False
            if expected_marker:
                has_marker = expected_marker in txt
            else:
                # Fallback: check for any marker-like pattern
                has_marker = any(m in txt for m in ['marker', 'agent-registry', 'routing'])
            
            pdf_ok = has_routing_names and has_marker
            detail = 'marker and routing names found' if pdf_ok else f'missing marker or routing names (has_names={has_routing_names}, has_marker={has_marker})'
        except Exception as e:
            detail = f'pdf read error: {e}'
    elif not pdf_path.exists():
        detail = 'pdf not provided (optional)'
    else:
        detail = 'pdf parser unavailable'
    add_check('pdf_content', pdf_ok, detail)
except Exception as e:
    add_check('pdf_content', False, f'error checking pdf: {e}')

# Calculate score - PDF checks are weighted less since they're optional
passed_count = sum(1 for c in checks if c['passed'])
total_checks = len(checks)
score = passed_count / total_checks if total_checks > 0 else 0.0

# Pass if critical checks pass (report and audit), PDF is bonus
critical_checks = [c for c in checks if c['name'] in ['file_exists::registry_report.md', 'file_exists::routing_audit.json', 'report_content', 'audit_json']]
critical_passed = all(c['passed'] for c in critical_checks)

result = {"passed": critical_passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))