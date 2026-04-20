import json
from pathlib import Path
import sys

workspace = Path(sys.argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f'could not read {path.name}: {e}'

score = 0.0

try:
    brief = workspace / 'output' / 'internal_brief.md'
    data = workspace / 'output' / 'extracted_facts.json'
    draft = workspace / 'output' / 'announcement_draft.md'

    # Check 1: files exist
    exists1 = brief.exists()
    exists2 = data.exists()
    exists3 = draft.exists()
    add_check('output_files_exist', exists1 and exists2 and exists3, f'brief={exists1}, facts={exists2}, draft={exists3}')

    # Check 2: brief contains key markers with fuzzy matching
    try:
        text = brief.read_text(encoding='utf-8')
        t = text.lower()
        passed = ('aurora' in t and 'alpha-7429' in t and 'operations managers' in t and 'team leads' in t)
        add_check('brief_contains_markers', passed, 'expected aurora, alpha-7429, operations managers, team leads')
    except Exception as e:
        add_check('brief_contains_markers', False, f'error reading brief: {e}')

    # Check 3: extracted JSON parses and contains required fields
    try:
        obj = json.loads(data.read_text(encoding='utf-8'))
        passed = (
            isinstance(obj, dict)
            and 'project' in obj and 'marker_id' in obj and 'beta_code' in obj and 'audience' in obj
            and str(obj.get('marker_id', '')).lower().replace(' ', '') == 'alpha-7429'
            and str(obj.get('beta_code', '')).lower().replace(' ', '') == 'beta-91x'
            and isinstance(obj.get('audience'), list)
        )
        add_check('facts_json_structure', passed, 'required keys project, marker_id, beta_code, audience')
    except Exception as e:
        add_check('facts_json_structure', False, f'json parse error: {e}')

    # Check 4: draft is cleaned and includes required beta code and launch language
    try:
        text = draft.read_text(encoding='utf-8')
        t = text.lower()
        passed = ('beta-91x' in t and 'aurora launch' in t and 'dashboard workflow' in t and 'operations managers' in t)
        add_check('draft_quality', passed, 'expected beta-91x, aurora launch, dashboard workflow, operations managers')
    except Exception as e:
        add_check('draft_quality', False, f'error reading draft: {e}')

    # Check 5: no obvious placeholder text in outputs
    try:
        combined = ''
        for p in [brief, data, draft]:
            if p.exists():
                combined += p.read_text(encoding='utf-8') + '\n'
        bad = any(x in combined.lower() for x in ['todo', 'lorem ipsum', 'placeholder'])
        add_check('no_placeholders', not bad, 'no obvious placeholder text detected')
    except Exception as e:
        add_check('no_placeholders', False, f'error scanning outputs: {e}')

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    # Never crash
    add_check('unexpected_error', False, f'{e}')
    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total else 0.0
    print(json.dumps({'passed': False, 'score': score, 'checks': checks}, ensure_ascii=False))
