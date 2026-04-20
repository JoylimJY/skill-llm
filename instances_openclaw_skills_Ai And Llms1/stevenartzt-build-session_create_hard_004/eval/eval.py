import json
import os
import re
import sys
from pathlib import Path

checks = []

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, f'Could not read {path}: {e}'

try:
    log_path = workspace / 'build_session_log.md'
    if log_path.exists():
        try:
            log_text = log_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            log_text = None
            add_check('log_readable', False, f'Log file exists but could not be read: {e}')
        else:
            add_check('log_readable', True, 'Log file exists and is readable.')
    else:
        log_text = None
        add_check('log_readable', False, 'build_session_log.md is missing.')

    if log_text:
        normalized = re.sub(r'[^a-z0-9]+', ' ', log_text.lower())
        has_title = 'build session' in normalized
        has_built = ('what i built' in normalized) or ('built' in normalized)
        has_insight = 'key insights' in normalized or 'insights' in normalized
        add_check('log_structure', has_title and has_built and has_insight,
                  'Expected session-log sections were found with fuzzy matching.' if (has_title and has_built and has_insight) else 'Missing one or more expected sections: title/what I built/key insights.')

        marker_hits = []
        for marker in ['BUILD_SESSION_MARKER_ALPHA', 'BUILD_SESSION_MARKER_BETA', 'BUILD_SESSION_MARKER_GAMMA', 'BUILD_SESSION_MARKER_PDF']:
            if marker.lower() in log_text.lower():
                marker_hits.append(marker)
        add_check('uses_input_markers', len(marker_hits) >= 1,
                  f'Marker references found: {", ".join(marker_hits) if marker_hits else "none"}.')
    else:
        add_check('log_structure', False, 'Cannot inspect structure because the log is missing or unreadable.')
        add_check('uses_input_markers', False, 'Cannot inspect marker usage because the log is missing or unreadable.')

    # Check for an actual tool/script in workspace root or subdirectories.
    candidate_files = []
    try:
        for pattern in ['*.py', '*.sh', '*.md', '*.txt']:
            candidate_files.extend(workspace.rglob(pattern))
    except Exception as e:
        add_check('workspace_scan', False, f'Workspace scan failed: {e}')
        candidate_files = []
    else:
        add_check('workspace_scan', True, f'Scanned workspace; found {len(candidate_files)} candidate files.')

    # Require at least one file with a clear build-session/actionable selection mention.
    actionable = False
    details = []
    for p in candidate_files:
        try:
            text = p.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        norm = re.sub(r'\s+', ' ', text.lower())
        if ('smallest useful task' in norm) or ('pick one thing' in norm) or ('blocker' in norm and 'urgent' in norm):
            actionable = True
            details.append(p.name)
    add_check('actionable_content', actionable, f'Actionable build-session content found in: {", ".join(details) if details else "none"}.')

    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks) if checks else 0.0
    passed = all(c['passed'] for c in checks)
except Exception as e:
    checks.append({"name": "fatal", "passed": False, "detail": f'Unexpected evaluator error: {e}'})
    score = 0.0
    passed = False

print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
