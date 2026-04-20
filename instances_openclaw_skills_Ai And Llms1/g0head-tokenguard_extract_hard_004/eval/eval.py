import json
import os
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
checks = []


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})


def safe_read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8')), None
    except Exception as e:
        return None, f'Failed to read/parse JSON: {e}'


def contains_term_recursive(obj, search_term):
    """Recursively search for a term in keys or values of a JSON structure"""
    search_term = search_term.lower()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if search_term in str(k).lower():
                return True
            if contains_term_recursive(v, search_term):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if contains_term_recursive(item, search_term):
                return True
    return False


try:
    out_path = workspace / 'tokenguard_audit.json'
    if out_path.exists():
        try:
            data = json.loads(out_path.read_text(encoding='utf-8'))
            add_check('output_exists_and_parseable', True, 'tokenguard_audit.json exists and is valid JSON')
        except Exception as e:
            data = None
            add_check('output_exists_and_parseable', False, f'File exists but is not valid JSON: {e}')
    else:
        data = None
        add_check('output_exists_and_parseable', False, 'tokenguard_audit.json is missing')

    session_path = workspace / 'tokenguard' / 'session.json'
    limit_path = workspace / 'tokenguard' / 'limit.json'

    session, session_err = (None, None)
    limit, limit_err = (None, None)
    try:
        session = json.loads(session_path.read_text(encoding='utf-8'))
    except Exception as e:
        session_err = e
    try:
        limit = json.loads(limit_path.read_text(encoding='utf-8'))
    except Exception as e:
        limit_err = e

    if session is None:
        add_check('input_session_available', False, f'session.json missing/malformed: {session_err}')
    else:
        add_check('input_session_available', True, 'session.json loaded')

    if limit is None:
        add_check('input_limit_available', False, f'limit.json missing/malformed: {limit_err}')
    else:
        add_check('input_limit_available', True, 'limit.json loaded')

    if isinstance(data, dict):
        # fuzzy-ish field checks - search recursively for terms in nested structures
        has_summary = contains_term_recursive(data, 'summary')
        has_spent = contains_term_recursive(data, 'spent')
        has_limit = contains_term_recursive(data, 'limit')
        has_entries = contains_term_recursive(data, 'entry') or contains_term_recursive(data, 'warn')
        add_check('output_contains_summary_fields', has_summary and has_spent and has_limit, f'keys={list(data.keys())}')
        add_check('output_mentions_entries_or_warnings', has_entries, f'keys={list(data.keys())}')

        # content verification with forgiving matching
        text = json.dumps(data, ensure_ascii=False).lower()
        expected_phrases = ['tokenguard', 'audit', 'spent', 'limit']
        phrase_hits = sum(1 for p in expected_phrases if p in text)
        add_check('output_contains_core_terms', phrase_hits >= 3, f'found {phrase_hits}/{len(expected_phrases)} expected terms')

        # Verify at least one marker from inputs is surfaced somewhere in output
        markers = ['marker_alpha', 'marker_beta', 'marker_gamma']
        marker_hits = sum(1 for m in markers if m in text)
        add_check('output_surfaces_input_markers', marker_hits >= 1, f'found {marker_hits} marker references')

        # If output includes any numeric summary, verify it is close to source values when present
        spent_ok = True
        limit_ok = True
        if session is not None:
            spent_src = session.get('spent_usd')
            limit_src = session.get('limit_usd') or (limit.get('current_limit_usd') if isinstance(limit, dict) else None)
            def fuzzy_num_check(source_val, blob):
                if source_val is None:
                    return True
                s = str(source_val)
                return s in blob or s.replace('.0', '') in blob
            spent_ok = fuzzy_num_check(spent_src, text)
            limit_ok = fuzzy_num_check(limit_src, text)
        add_check('output_numeric_values_reflect_inputs', spent_ok and limit_ok, 'numeric values appear to match input session/limit')
    else:
        add_check('output_contains_summary_fields', False, 'output is not a JSON object')
        add_check('output_mentions_entries_or_warnings', False, 'output is not a JSON object')
        add_check('output_contains_core_terms', False, 'output is not a JSON object')
        add_check('output_surfaces_input_markers', False, 'output is not a JSON object')
        add_check('output_numeric_values_reflect_inputs', False, 'output is not a JSON object')

except Exception as e:
    add_check('eval_internal_error', False, f'Unexpected evaluator error handled gracefully: {e}')

passed = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {'passed': passed, 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))