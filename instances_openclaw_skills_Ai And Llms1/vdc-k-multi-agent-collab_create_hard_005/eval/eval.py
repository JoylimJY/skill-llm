import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)

marker = 'atlas-marker-7f3'
required_files = ['TASK.md', 'CHANGELOG.md', 'CONTEXT.md', 'WEEKLY-REPORT.md']

try:
    missing = [f for f in required_files if not (workspace / f).exists()]
    add_check('required_files_exist', len(missing) == 0, 'missing: ' + ', '.join(missing) if missing else 'all required files present')
except Exception as e:
    add_check('required_files_exist', False, f'error: {e}')

# TASK.md checks
try:
    txt, err = safe_read(workspace / 'TASK.md')
    if txt is None:
        add_check('task_file_readable', False, f'could not read TASK.md: {err}')
    else:
        norm = txt.lower()
        task_lines = [ln for ln in txt.splitlines() if re.search(r'\btask\b|\[ \]|\[x\]|done|blocked', ln, re.I)]
        done_count = len(re.findall(r'\b(?:done|\[x\])\b', norm, re.I))
        blocked_count = len(re.findall(r'\bblocked\b', norm, re.I))
        add_check('task_count', len(task_lines) >= 7, f'found {len(task_lines)} likely task lines')
        add_check('task_done_count', done_count >= 2, f'found {done_count} done markers')
        add_check('task_blocked_count', blocked_count >= 2, f'found {blocked_count} blocked markers')
        add_check('task_marker', marker in norm, 'marker present' if marker in norm else 'marker missing')
except Exception as e:
    add_check('task_checks', False, f'error: {e}')

# CHANGELOG.md checks
try:
    txt, err = safe_read(workspace / 'CHANGELOG.md')
    if txt is None:
        add_check('changelog_file_readable', False, f'could not read CHANGELOG.md: {err}')
    else:
        norm = txt.lower()
        entries = [ln for ln in txt.splitlines() if re.search(r'#\w+', ln)]
        tags = set(re.findall(r'#([a-z0-9_-]+)', norm))
        identities = len(re.findall(r'\bby\s+[a-z0-9_-]+', norm, re.I))
        add_check('changelog_entry_count', len(entries) >= 6, f'found {len(entries)} tagged lines')
        add_check('changelog_tags', len(tags) >= 3, f'found tags: {sorted(tags)}')
        add_check('changelog_identities', identities >= 3, f'found {identities} identity mentions')
        add_check('changelog_marker', marker in norm, 'marker present' if marker in norm else 'marker missing')
except Exception as e:
    add_check('changelog_checks', False, f'error: {e}')

# CONTEXT.md checks
try:
    txt, err = safe_read(workspace / 'CONTEXT.md')
    if txt is None:
        add_check('context_file_readable', False, f'could not read CONTEXT.md: {err}')
    else:
        norm = txt.lower()
        has_arch = bool(re.search(r'architecture decision|decision', norm, re.I))
        has_risk = bool(re.search(r'risk', norm, re.I))
        has_qmd = 'qmd' in norm
        add_check('context_architecture_decision', has_arch, 'architecture decision found' if has_arch else 'missing')
        add_check('context_risk_note', has_risk, 'risk note found' if has_risk else 'missing')
        add_check('context_qmd_hint', has_qmd, 'qmd mentioned' if has_qmd else 'missing qmd')
        add_check('context_marker', marker in norm, 'marker present' if marker in norm else 'marker missing')
except Exception as e:
    add_check('context_checks', False, f'error: {e}')

# WEEKLY-REPORT.md checks
try:
    txt, err = safe_read(workspace / 'WEEKLY-REPORT.md')
    if txt is None:
        add_check('weekly_file_readable', False, f'could not read WEEKLY-REPORT.md: {err}')
    else:
        norm = txt.lower()
        has_pattern = 'pattern discovery' in norm
        has_candidate = bool(re.search(r'candidate skill', norm, re.I))
        repeated_ops = len(re.findall(r'update task|append changelog|qmd query', norm, re.I))
        add_check('weekly_pattern_section', has_pattern, 'pattern discovery section found' if has_pattern else 'missing')
        add_check('weekly_candidate_skill', has_candidate, 'candidate skill mentioned' if has_candidate else 'missing')
        add_check('weekly_repeated_operation', repeated_ops >= 1, f'found {repeated_ops} repeated-operation mentions')
        add_check('weekly_marker', marker in norm, 'marker present' if marker in norm else 'marker missing')
except Exception as e:
    add_check('weekly_checks', False, f'error: {e}')

# Final scoring
passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
passed = all(c['passed'] for c in checks)
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
