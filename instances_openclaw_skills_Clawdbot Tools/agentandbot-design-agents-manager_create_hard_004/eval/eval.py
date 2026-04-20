import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, e

try:
    report_path = workspace / 'routing_audit_report.txt'
    if report_path.exists():
        report = report_path.read_text(encoding='utf-8', errors='replace')
        normalized = re.sub(r'\s+', ' ', report.lower())
        marker_ok = 'routing_audit_marker' in normalized
        add_check('report_exists_and_contains_marker', marker_ok, 'found' if marker_ok else 'missing marker string or report content')
    else:
        add_check('report_exists_and_contains_marker', False, 'routing_audit_report.txt is missing')
except Exception as e:
    add_check('report_exists_and_contains_marker', False, f'error reading report: {e}')

try:
    reg_path = workspace / 'references' / 'agent-registry.md'
    if reg_path.exists():
        reg = reg_path.read_text(encoding='utf-8', errors='replace')
        low = reg.lower()
        has_agent = 'routing-inspector' in low
        add_check('registry_mentions_new_agent', has_agent, 'routing-inspector present' if has_agent else 'routing-inspector not found')

        table_ok = bool(re.search(r'\|\s*routing-inspector\s*\|', low, re.I))
        add_check('registry_table_row_added', table_ok, 'table row found' if table_ok else 'no table row for routing-inspector')

        profile_ok = bool(re.search(r'###\s*routing-inspector\b', reg, re.I)) and ('**Capabilities:**' in reg or '**Capabilities**' in reg)
        add_check('registry_profile_added', profile_ok, 'profile section found' if profile_ok else 'profile section missing')
    else:
        add_check('registry_mentions_new_agent', False, 'references/agent-registry.md missing')
        add_check('registry_table_row_added', False, 'references/agent-registry.md missing')
        add_check('registry_profile_added', False, 'references/agent-registry.md missing')
except Exception as e:
    add_check('registry_mentions_new_agent', False, f'error: {e}')
    add_check('registry_table_row_added', False, f'error: {e}')
    add_check('registry_profile_added', False, f'error: {e}')

try:
    report_path = workspace / 'routing_audit_report.txt'
    if report_path.exists():
        report = report_path.read_text(encoding='utf-8', errors='replace').lower()
        q1 = ('can assign' in report or 'assign to' in report) and 'routing-inspector' in report
        q2 = 'requires approval' in report or 'approval' in report
        q3 = 'escalation' in report and ('human' in report or 'ilkerkaan' in report or 'main' in report)
        add_check('report_summarizes_assigners', q1, 'assignment summary present' if q1 else 'assignment summary missing or weak')
        add_check('report_mentions_approval', q2, 'approval mentioned' if q2 else 'approval not mentioned')
        add_check('report_mentions_escalation_path', q3, 'escalation path mentioned' if q3 else 'escalation path missing')
    else:
        add_check('report_summarizes_assigners', False, 'report missing')
        add_check('report_mentions_approval', False, 'report missing')
        add_check('report_mentions_escalation_path', False, 'report missing')
except Exception as e:
    add_check('report_summarizes_assigners', False, f'error: {e}')
    add_check('report_mentions_approval', False, f'error: {e}')
    add_check('report_mentions_escalation_path', False, f'error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))