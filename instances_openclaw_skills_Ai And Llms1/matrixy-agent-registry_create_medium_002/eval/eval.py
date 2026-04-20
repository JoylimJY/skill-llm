import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def norm(s):
    return ''.join(ch.lower() for ch in s if ch.isalnum() or ch.isspace())


def main():
    checks = []
    total = 4
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    try:
        agent_audit_path = workspace / 'agent_audit.json'
        if not agent_audit_path.exists():
            checks.append({'name': 'agent_audit_exists', 'passed': False, 'detail': 'agent_audit.json is missing'})
        else:
            raw, err = safe_read_text(agent_audit_path)
            if raw is None:
                checks.append({'name': 'agent_audit_exists', 'passed': False, 'detail': f'Could not read agent_audit.json: {err}'})
            else:
                try:
                    data = json.loads(raw)
                    names = data.get('agents', []) if isinstance(data, dict) else []
                    security_flags = data.get('security_flags', []) if isinstance(data, dict) else []
                    ok_names = isinstance(names, list) and len(names) >= 4
                    found_security = False
                    for item in security_flags if isinstance(security_flags, list) else []:
                        text = norm(str(item))
                        if 'securityauditor' in text or 'authdebugger' in text:
                            found_security = True
                    checks.append({'name': 'agent_audit_structure', 'passed': ok_names and found_security, 'detail': f'agents={len(names) if isinstance(names, list) else "n/a"}, security_flags_found={found_security}'})
                except Exception as e:
                    checks.append({'name': 'agent_audit_structure', 'passed': False, 'detail': f'Invalid JSON or structure: {e}'})
    except Exception as e:
        checks.append({'name': 'agent_audit_exists', 'passed': False, 'detail': f'Unexpected error: {e}'})

    try:
        summary_path = workspace / 'summary.txt'
        if not summary_path.exists():
            checks.append({'name': 'summary_exists', 'passed': False, 'detail': 'summary.txt is missing'})
        else:
            raw, err = safe_read_text(summary_path)
            if raw is None:
                checks.append({'name': 'summary_exists', 'passed': False, 'detail': f'Could not read summary.txt: {err}'})
            else:
                t = norm(raw)
                has_count = bool(re.search(r'\b4\b', t))
                mentions_security = 'security' in t or 'authentication' in t or 'auth' in t
                checks.append({'name': 'summary_content', 'passed': has_count and mentions_security, 'detail': f'count_mentions={has_count}, security_mentions={mentions_security}'})
    except Exception as e:
        checks.append({'name': 'summary_content', 'passed': False, 'detail': f'Unexpected error: {e}'})

    try:
        marker_path = workspace / 'registry.json'
        if not marker_path.exists():
            checks.append({'name': 'marker_file_present', 'passed': False, 'detail': 'registry.json is missing'})
        else:
            raw, err = safe_read_text(marker_path)
            if raw is None:
                checks.append({'name': 'marker_file_present', 'passed': False, 'detail': f'Could not read registry.json: {err}'})
            else:
                try:
                    data = json.loads(raw)
                    marker = str(data.get('marker', ''))
                    passed = 'REGISTRY_MARKER_ABC123'.lower() in marker.lower()
                    checks.append({'name': 'marker_match', 'passed': passed, 'detail': f'marker_present={passed}'})
                except Exception as e:
                    checks.append({'name': 'marker_match', 'passed': False, 'detail': f'Invalid JSON: {e}'})
    except Exception as e:
        checks.append({'name': 'marker_match', 'passed': False, 'detail': f'Unexpected error: {e}'})

    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
