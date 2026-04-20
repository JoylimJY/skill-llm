from pathlib import Path
import json
import re
import sys

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

def safe_read(path):
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, f"Failed to read {path.name}: {e}"

required_files = ['TASK.md', 'CHANGELOG.md', 'CONTEXT.md', 'WEEKLY-REPORT.md', 'llms.txt']
for fname in required_files:
    p = workspace / fname
    try:
        exists = p.exists()
        add_check(f"exists:{fname}", exists, f"{'found' if exists else 'missing'}")
    except Exception as e:
        add_check(f"exists:{fname}", False, f"error checking existence: {e}")

contents = {}
for fname in required_files:
    p = workspace / fname
    try:
        text = p.read_text(encoding='utf-8', errors='ignore')
        contents[fname] = text
    except Exception as e:
        contents[fname] = None
        add_check(f"read:{fname}", False, f"read failed: {e}")

# Marker checks
for fname in required_files:
    text = contents.get(fname)
    try:
        passed = bool(text) and ('nebula_sync_marker' in re.sub(r'\s+', '', text.lower()))
        add_check(f"marker:{fname}", passed, "marker present" if passed else "marker missing")
    except Exception as e:
        add_check(f"marker:{fname}", False, f"error checking marker: {e}")

# TASK.md should have at least one checkbox task
try:
    text = contents.get('TASK.md') or ''
    passed = bool(re.search(r'\[\s*[ xX]\s*\]', text))
    add_check('task_has_checkbox', passed, 'checkbox task found' if passed else 'no checkbox task found')
except Exception as e:
    add_check('task_has_checkbox', False, f'error: {e}')

# CHANGELOG.md should have a tag-like token
try:
    text = contents.get('CHANGELOG.md') or ''
    passed = bool(re.search(r'#[A-Za-z0-9_\-]+', text))
    add_check('changelog_has_tag', passed, 'tag found' if passed else 'no tag found')
except Exception as e:
    add_check('changelog_has_tag', False, f'error: {e}')

# CONTEXT.md should mention a decision log or decision
try:
    text = contents.get('CONTEXT.md') or ''
    low = text.lower()
    passed = ('decision' in low) and ('task' in low)
    add_check('context_has_decision_notes', passed, 'decision notes found' if passed else 'missing decision notes')
except Exception as e:
    add_check('context_has_decision_notes', False, f'error: {e}')

# WEEKLY-REPORT.md should include pattern discovery and candidate skill
try:
    text = contents.get('WEEKLY-REPORT.md') or ''
    low = re.sub(r'\s+', ' ', text.lower())
    passed = ('pattern discovery' in low) and ('candidate skill' in low)
    add_check('weekly_report_pattern_section', passed, 'pattern discovery section found' if passed else 'missing pattern discovery content')
except Exception as e:
    add_check('weekly_report_pattern_section', False, f'error: {e}')

# llms.txt should list the core files
try:
    text = contents.get('llms.txt') or ''
    low = text.lower()
    expected_mentions = ['task.md', 'changelog.md', 'context.md', 'weekly-report.md']
    passed = all(item in low for item in expected_mentions)
    add_check('llms_lists_core_files', passed, 'all core files listed' if passed else 'missing one or more core files')
except Exception as e:
    add_check('llms_lists_core_files', False, f'error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
