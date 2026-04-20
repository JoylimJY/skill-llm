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
    report_path = workspace / 'report.json'
    if not report_path.exists():
        add_check('report_exists', False, 'report.json is missing')
        report = None
    else:
        try:
            report = json.loads(report_path.read_text(encoding='utf-8'))
            add_check('report_exists', True, 'report.json found and parsed')
        except Exception as e:
            report = None
            add_check('report_exists', False, f'report.json is present but invalid JSON: {e}')

    skill_name_ok = False
    if isinstance(report, dict):
        skill_name = str(report.get('skill_name', ''))
        skill_name_ok = 'pincer' in skill_name.lower()
        add_check('skill_name', skill_name_ok, f"skill_name={skill_name!r}")
    else:
        add_check('skill_name', False, 'report content unavailable')

    risk_ok = False
    if isinstance(report, dict):
        risk = str(report.get('risk_level', report.get('risk', '')))
        risk_ok = any(x in risk.lower() for x in ['danger', 'warning', 'caution', 'clean'])
        add_check('risk_level_present', risk_ok, f"risk_level={risk!r}")
    else:
        add_check('risk_level_present', False, 'report content unavailable')

    findings_ok = False
    if isinstance(report, dict):
        findings = report.get('findings', [])
        if isinstance(findings, list):
            joined = ' '.join([str(x) for x in findings]).lower()
            findings_ok = any(term in joined for term in ['binary', 'pattern', 'binary check', 'suspicious', 'marker'])
            add_check('findings_list', findings_ok, f'findings_count={len(findings)}')
        else:
            add_check('findings_list', False, f'findings has type {type(findings).__name__}')
    else:
        add_check('findings_list', False, 'report content unavailable')

    content_ok = False
    try:
        skill_md = (workspace / 'skill' / 'SKILL.md').read_text(encoding='utf-8', errors='replace')
        markers = ['marker-alpha', 'marker-beta', 'marker-gamma']
        lowered = skill_md.lower() + ' ' + (workspace / 'skill' / 'README.txt').read_text(encoding='utf-8', errors='replace').lower() + ' ' + (workspace / 'manifest.json').read_text(encoding='utf-8', errors='replace').lower()
        content_ok = all(m in lowered for m in markers)
        add_check('input_markers_present', content_ok, 'expected markers checked across input files')
    except Exception as e:
        add_check('input_markers_present', False, f'error reading inputs: {e}')

    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    score = passed / total if total else 0.0
    result = {"passed": passed == total, "score": score, "checks": checks}
    print(json.dumps(result))
except Exception as e:
    checks.append({"name": "fatal_error", "passed": False, "detail": str(e)})
    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    score = passed / total if total else 0.0
    print(json.dumps({"passed": False, "score": score, "checks": checks}))