import json
import os
import re
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def norm(s: str) -> str:
    """Normalize string for fuzzy matching - lowercase and collapse whitespace."""
    s = s.lower()
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def fuzzy_contains(haystack: str, needles):
    """Check if all needles appear in haystack (case-insensitive)."""
    h = norm(haystack)
    return all(norm(n) in h for n in needles)


def find_file(workspace: Path, filename: str) -> Path:
    """Find a file in workspace root or workspace_out subdirectory."""
    candidates = [
        workspace / filename,
        workspace / 'workspace_out' / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def main():
    import sys
    workspace = Path(sys.argv[1])
    checks = []
    passed_count = 0

    def add_check(name, passed, detail):
        nonlocal passed_count
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            passed_count += 1

    # 1) CHANGELOG.md exists and mentions key operational points
    try:
        p = find_file(workspace, 'CHANGELOG.md')
        if p is None:
            add_check('changelog_exists', False, 'CHANGELOG.md is missing')
        else:
            text, err = safe_read(p)
            if text is None:
                add_check('changelog_exists', False, f'Could not read CHANGELOG.md: {err}')
            else:
                # Check for required operational references from prompt
                has_validation_boundary = fuzzy_contains(text, ['validation boundary', 'static checks'])
                has_restart = fuzzy_contains(text, ['gateway restart'])
                has_rollback = fuzzy_contains(text, ['revert_reply_footer.py'])
                
                ok = has_validation_boundary and has_restart and has_rollback
                add_check('changelog_content', ok, 'Found required operational references' if ok else 'Missing one or more required references')
    except Exception as e:
        add_check('changelog_exists', False, f'Unexpected error: {e}')

    # 2) verification_summary.json exists and is parseable with expected fields
    try:
        p = find_file(workspace, 'verification_summary.json')
        if p is None:
            add_check('summary_exists', False, 'verification_summary.json is missing')
        else:
            try:
                data = json.loads(p.read_text(encoding='utf-8'))
                # Accept multiple key naming conventions for target file
                target_keys = ['target_file', 'target_file_discovered', 'discovered_target_file']
                target_key = next((k for k in target_keys if k in data), None)
                
                # Accept multiple key naming conventions for live acceptance
                live_keys = ['live_accepted', 'live_telegram_acceptance_confirmed', 'live_acceptance_confirmed']
                live_key = next((k for k in live_keys if k in data), None)
                
                # Check for required fields with flexible naming
                keys_ok = (
                    target_key is not None and
                    'dry_run_performed' in data and
                    'verify_performed' in data and
                    live_key is not None
                )
                
                content_ok = False
                if keys_ok:
                    tf = str(data.get(target_key, ''))
                    live_val = data.get(live_key) if live_key else None
                    dry_run_val = data.get('dry_run_performed')
                    verify_val = data.get('verify_performed')
                    
                    content_ok = (
                        'agent-runner.runtime' in tf.lower() and
                        bool(dry_run_val) and
                        bool(verify_val) and
                        (live_val is False)
                    )
                
                add_check('summary_content', keys_ok and content_ok, 'Summary fields and values look correct' if keys_ok and content_ok else 'Missing field or unexpected value in summary')
            except Exception as e:
                add_check('summary_content', False, f'Could not parse verification_summary.json: {e}')
    except Exception as e:
        add_check('summary_exists', False, f'Unexpected error: {e}')

    # 3) rollback_note.txt exists and references both rollback and restart guidance
    try:
        p = find_file(workspace, 'rollback_note.txt')
        if p is None:
            add_check('rollback_exists', False, 'rollback_note.txt is missing')
        else:
            text, err = safe_read(p)
            if text is None:
                add_check('rollback_exists', False, f'Could not read rollback_note.txt: {err}')
            else:
                ok = fuzzy_contains(text, ['revert_reply_footer.py']) and fuzzy_contains(text, ['openclaw gateway restart'])
                add_check('rollback_content', ok, 'Rollback note includes revert and restart guidance' if ok else 'Rollback note is incomplete')
    except Exception as e:
        add_check('rollback_exists', False, f'Unexpected error: {e}')

    # 4) At least one generated file should preserve the marker tokens in a way that can be verified
    try:
        marker_file = workspace / 'input_marker.json'
        if not marker_file.exists():
            add_check('marker_file', False, 'input_marker.json is missing')
        else:
            data = json.loads(marker_file.read_text(encoding='utf-8'))
            tokens = data.get('footer_tokens', [])
            ok = isinstance(tokens, list) and len(tokens) >= 3 and all(any(ch in str(tok) for ch in ['🧠', '💭', '📊']) or 'Think' in str(tok) for tok in tokens)
            add_check('marker_tokens', ok, 'Marker tokens are present and readable' if ok else 'Marker tokens are missing or malformed')
    except Exception as e:
        add_check('marker_tokens', False, f'Could not inspect marker file: {e}')

    total = len(checks)
    score = (passed_count / total) if total else 0.0
    result = {
        'passed': passed_count == total,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()