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


def normalize(s):
    return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()


def check_output_exists(workspace):
    p = Path(workspace) / 'output.txt'
    try:
        if not p.exists():
            return False, 'output.txt is missing'
        txt = p.read_text(encoding='utf-8', errors='replace')
        if not txt.strip():
            return False, 'output.txt is empty'
        return True, 'output.txt exists and is non-empty'
    except Exception as e:
        return False, f'could not read output.txt: {e}'


def check_mentions_risk_and_evidence(workspace):
    p = Path(workspace) / 'output.txt'
    try:
        txt = p.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return False, f'could not read output.txt: {e}'

    n = normalize(txt)
    risk_terms = ['danger', 'malware', 'blocked', 'caution', 'clean']
    has_risk = any(term in n for term in risk_terms)
    evidence_terms = ['base64', 'curl', 'hidden', 'marker', 'suspicious', 'shell']
    has_evidence = any(term in n for term in evidence_terms)
    if not has_risk:
        return False, 'no risk classification found in report'
    if not has_evidence:
        return False, 'no evidence keywords found in report'
    return True, 'report includes a risk classification and evidence'


def check_workspace_markers(workspace):
    try:
        skill_md = Path(workspace) / 'sample-skill' / 'SKILL.md'
        hidden = Path(workspace) / 'sample-skill' / '.hidden_marker'
        cfg = Path(workspace) / 'sample-skill' / 'config.json'
        readme = Path(workspace) / 'readme.txt'
        texts = []
        for p in [skill_md, hidden, cfg, readme]:
            try:
                texts.append(p.read_text(encoding='utf-8', errors='replace'))
            except Exception:
                texts.append('')
        joined = '\n'.join(texts)
        if 'MARKER:HIDDEN_FILE_PRESENT' not in joined:
            return False, 'hidden file marker not found in inputs'
        if 'MARKER:CONFIG_JSON_PRESENT' not in joined:
            return False, 'config marker not found in inputs'
        if 'MARKER:WORKSPACE_READY' not in joined:
            return False, 'workspace marker not found in inputs'
        return True, 'expected marker content found in generated inputs'
    except Exception as e:
        return False, f'failed while checking markers: {e}'


def main():
    checks = []
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'

    passed, detail = check_output_exists(workspace)
    checks.append({'name': 'output_exists', 'passed': passed, 'detail': detail})

    passed2, detail2 = check_mentions_risk_and_evidence(workspace)
    checks.append({'name': 'output_mentions_risk_and_evidence', 'passed': passed2, 'detail': detail2})

    passed3, detail3 = check_workspace_markers(workspace)
    checks.append({'name': 'input_markers_present', 'passed': passed3, 'detail': detail3})

    score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
    result = {
        'passed': all(c['passed'] for c in checks),
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': str(e)}]}, ensure_ascii=False))
