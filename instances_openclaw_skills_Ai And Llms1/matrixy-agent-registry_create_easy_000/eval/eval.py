import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)

try:
    expected_dir = workspace / '.claude' / 'skills' / 'agent-registry'
    add_check('registry_dir_exists', expected_dir.exists(), f"exists={expected_dir.exists()}")
except Exception as e:
    add_check('registry_dir_exists', False, f'error: {e}')

try:
    a = workspace / 'agents' / 'security-auditor.md'
    b = workspace / '.claude' / 'agents' / 'code-reviewer.md'
    ok_a = a.exists()
    ok_b = b.exists()
    add_check('seed_agent_files_exist', ok_a and ok_b, f"security-auditor={ok_a}, code-reviewer={ok_b}")
except Exception as e:
    add_check('seed_agent_files_exist', False, f'error: {e}')

try:
    text_a, err_a = safe_read(workspace / 'agents' / 'security-auditor.md')
    text_b, err_b = safe_read(workspace / '.claude' / 'agents' / 'code-reviewer.md')
    found_a = bool(text_a and re.search(r'registry-marker-sec-001', text_a, re.I))
    found_b = bool(text_b and re.search(r'registry-marker-rev-002', text_b, re.I))
    detail = []
    if err_a:
        detail.append(f'a_read_error={err_a}')
    if err_b:
        detail.append(f'b_read_error={err_b}')
    detail.append(f'marker_a={found_a}, marker_b={found_b}')
    add_check('marker_content_present', found_a and found_b, '; '.join(detail))
except Exception as e:
    add_check('marker_content_present', False, f'error: {e}')

try:
    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    score = passed / total if total else 0.0
    result = {"passed": passed == total, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "eval_fatal", "passed": False, "detail": str(e)}]}))
