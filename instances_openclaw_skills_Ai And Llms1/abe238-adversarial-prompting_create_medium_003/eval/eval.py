import json
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)

# Check 1: marker file exists and contains expected marker
try:
    marker_path = workspace / 'task_marker.txt'
    if not marker_path.exists():
        add_check('marker file exists', False, 'task_marker.txt is missing')
    else:
        txt = marker_path.read_text(encoding='utf-8', errors='replace')
        passed = 'ADV_PROMPTING_MEDIUM_2025' in txt and 'consolidation-debugging' in txt
        add_check('marker file exists', passed, 'marker content verified' if passed else f'unexpected content: {txt[:120]!r}')
except Exception as e:
    add_check('marker file exists', False, f'error reading marker file: {e}')

# Check 2: PDF exists and contains marker text
try:
    pdf_path = workspace / 'reference_brief.pdf'
    if not pdf_path.exists():
        add_check('pdf exists', False, 'reference_brief.pdf is missing')
    else:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(str(pdf_path))
            text = ''
            for page in reader.pages:
                try:
                    text += page.extract_text() or ''
                except Exception:
                    pass
            passed = 'ADV_PROMPTING_MEDIUM_2025' in text and 'Fix A' in text and 'Fix B' in text
            add_check('pdf marker text', passed, 'pdf text verified' if passed else f'pdf text missing markers; extracted snippet: {text[:200]!r}')
        except Exception as e:
            add_check('pdf marker text', False, f'could not parse pdf: {e}')
except Exception as e:
    add_check('pdf marker text', False, f'error handling pdf: {e}')

# Check 3: user request file exists and is semantically close to expected purpose
try:
    req_path = workspace / 'user_request.txt'
    if not req_path.exists():
        add_check('user request exists', False, 'user_request.txt is missing')
    else:
        txt = req_path.read_text(encoding='utf-8', errors='replace')
        norm = re.sub(r'[^a-z0-9]+', ' ', txt.lower())
        keywords = ['analyze', 'weakness', 'validate', 'recommend']
        passed = all(k in norm for k in keywords)
        add_check('user request exists', passed, 'request content matches intent' if passed else f'content not aligned: {txt[:180]!r}')
except Exception as e:
    add_check('user request exists', False, f'error reading user request: {e}')

# Check 4: task bundle directory exists with required structure
try:
    task_bundle_path = workspace / 'task_bundle'
    if not task_bundle_path.exists():
        add_check('task bundle directory', False, 'task_bundle directory is missing')
    else:
        # Check for required files in task bundle
        required_files = [
            task_bundle_path / 'task.md',
            task_bundle_path / 'evaluation_criteria.json',
            task_bundle_path / 'context'
        ]
        
        missing_files = [f.name for f in required_files if not f.exists()]
        
        if missing_files:
            add_check('task bundle structure', False, f'missing required files/dirs: {missing_files}')
        else:
            # Verify task.md has substantive content
            task_md = task_bundle_path / 'task.md'
            content = task_md.read_text(encoding='utf-8', errors='replace')
            norm = re.sub(r'\s+', ' ', content.strip().lower())
            
            # Check for key elements expected in adversarial prompting task
            key_terms = ['fix', 'vulnerability', 'recommend', 'analysis']
            has_terms = any(term in norm for term in key_terms)
            
            # Check evaluation_criteria.json is valid JSON with required fields
            eval_criteria = task_bundle_path / 'evaluation_criteria.json'
            try:
                criteria_data = json.loads(eval_criteria.read_text(encoding='utf-8', errors='replace'))
                has_required_fields = all(k in criteria_data for k in ['task_id', 'skill', 'required_elements'])
            except Exception:
                has_required_fields = False
            
            passed = has_terms and has_required_fields and len(content) >= 200
            add_check('task bundle structure', passed, 'task bundle verified with required structure' if passed else f'content validation failed: has_terms={has_terms}, has_fields={has_required_fields}, len={len(content)}')
except Exception as e:
    add_check('task bundle structure', False, f'error checking task bundle: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))