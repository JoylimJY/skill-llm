import json
import os
import re
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return ''.join(ch.lower() for ch in s if ch.isalnum() or ch.isspace())
    except Exception:
        return ''


def find_number(text, labels):
    try:
        low = text.lower()
        for label in labels:
            idx = low.find(label.lower())
            if idx >= 0:
                snippet = text[idx:idx + 120]
                # For "top" or "most expensive" labels, look for dollar amounts first
                # to avoid matching the count in headers like "TOP 3"
                if 'top' in label.lower() or 'most expensive' in label.lower():
                    # Try to find a dollar amount pattern first
                    m = re.search(r'\$?[-+]?[0-9]*\.?[0-9]+', snippet)
                    if m:
                        val = float(m.group(0))
                        # If we found a small integer (likely a count), keep searching
                        if val < 5 and val == int(val):
                            # Search for the next number that looks like an amount
                            remaining = snippet[m.end():]
                            m2 = re.search(r'\$?[-+]?[0-9]*\.?[0-9]+', remaining)
                            if m2:
                                return float(m2.group(0))
                        return val
                else:
                    m = re.search(r'([-+]?[0-9]*\.?[0-9]+)', snippet)
                    if m:
                        return float(m.group(1))
    except Exception:
        return None
    return None


def get_value_flexible(data, possible_keys, default=None):
    """Try multiple possible key names to find a value."""
    for key in possible_keys:
        if key in data:
            return data[key]
    return default


def main(workspace_dir):
    checks = []
    ws = Path(workspace_dir)
    report_txt = ws / 'tokenguard_summary.txt'
    report_json = ws / 'tokenguard_summary.json'
    session_path = ws / '.tokenguard' / 'session.json'
    limit_path = ws / '.tokenguard' / 'limit.json'
    marker_path = ws / 'marker_tokenguard_seed.txt'

    # Check 1: output txt exists
    try:
        exists = report_txt.exists()
        checks.append({
            'name': 'summary_txt_exists',
            'passed': bool(exists),
            'detail': 'tokenguard_summary.txt found' if exists else 'tokenguard_summary.txt is missing'
        })
    except Exception as e:
        checks.append({'name': 'summary_txt_exists', 'passed': False, 'detail': f'error checking file existence: {e}'})

    # Check 2: output json exists
    try:
        exists = report_json.exists()
        checks.append({
            'name': 'summary_json_exists',
            'passed': bool(exists),
            'detail': 'tokenguard_summary.json found' if exists else 'tokenguard_summary.json is missing'
        })
    except Exception as e:
        checks.append({'name': 'summary_json_exists', 'passed': False, 'detail': f'error checking file existence: {e}'})

    # Load source data
    session = None
    limit = None
    session_err = None
    limit_err = None
    try:
        if session_path.exists():
            session = json.loads(session_path.read_text(encoding='utf-8'))
        else:
            session_err = 'missing session.json'
    except Exception as e:
        session_err = str(e)
    try:
        if limit_path.exists():
            limit = json.loads(limit_path.read_text(encoding='utf-8'))
        else:
            limit_err = 'missing limit.json'
    except Exception as e:
        limit_err = str(e)

    expected_limit = 25.0
    expected_spent = 13.75
    expected_remaining = 11.25
    expected_warning_pct = 0.8
    expected_warning_threshold = 20.0  # 80% of 25
    expected_entries = 4
    expected_top = 6.0

    # Check 3: text includes key values
    try:
        txt = report_txt.read_text(encoding='utf-8', errors='replace') if report_txt.exists() else ''
        norm = normalize(txt)
        required_phrases = ['current limit', 'total spent', 'remaining budget', 'warning threshold', 'log entries']
        phrase_ok = all(normalize(p) in norm for p in required_phrases)
        
        # flexible numeric checks
        limit_found = find_number(txt, ['current limit', 'limit'])
        spent_found = find_number(txt, ['total spent', 'spent'])
        remaining_found = find_number(txt, ['remaining budget', 'remaining'])
        entries_found = find_number(txt, ['log entries', 'entries'])
        top_found = find_number(txt, ['top', 'most expensive'])
        
        details = []
        details.append(f'phrases={phrase_ok}')
        details.append(f'limit={limit_found}')
        details.append(f'spent={spent_found}')
        details.append(f'remaining={remaining_found}')
        details.append(f'entries={entries_found}')
        details.append(f'top={top_found}')
        
        passed = phrase_ok and (
            limit_found is not None and abs(limit_found - expected_limit) < 0.2 and
            spent_found is not None and abs(spent_found - expected_spent) < 0.2 and
            remaining_found is not None and abs(remaining_found - expected_remaining) < 0.2 and
            entries_found is not None and abs(entries_found - expected_entries) < 1.0 and
            top_found is not None and abs(top_found - expected_top) < 0.2
        )
        checks.append({'name': 'summary_txt_content', 'passed': passed, 'detail': '; '.join(details)})
    except Exception as e:
        checks.append({'name': 'summary_txt_content', 'passed': False, 'detail': f'error reading/parsing txt: {e}'})

    # Check 4: json structure and values (flexible key names)
    try:
        data = json.loads(report_json.read_text(encoding='utf-8', errors='replace')) if report_json.exists() else {}
        
        # Accept multiple possible key names for each field
        limit_keys = ['current_limit', 'limit', 'budget_limit']
        spent_keys = ['total_spent', 'spent', 'total']
        remaining_keys = ['remaining_budget', 'remaining', 'budget_remaining']
        warning_keys = ['warning_threshold', 'warning', 'threshold']
        entry_count_keys = ['entry_count', 'num_log_entries', 'num_entries', 'log_entries', 'entries']
        top_keys = ['top_entries', 'top_3_entries', 'top3_entries', 'top3']
        
        current_limit = get_value_flexible(data, limit_keys)
        total_spent = get_value_flexible(data, spent_keys)
        remaining_budget = get_value_flexible(data, remaining_keys)
        warning_threshold = get_value_flexible(data, warning_keys)
        entry_count = get_value_flexible(data, entry_count_keys)
        top_entries = get_value_flexible(data, top_keys)
        
        has_keys = all([
            current_limit is not None,
            total_spent is not None,
            remaining_budget is not None,
            warning_threshold is not None,
            entry_count is not None,
            top_entries is not None
        ])
        
        vals_ok = False
        if has_keys:
            try:
                # Accept both percentage (0.8) and dollar amount (20.0) for warning threshold
                warning_ok = (
                    abs(float(warning_threshold) - expected_warning_pct) < 0.01 or
                    abs(float(warning_threshold) - expected_warning_threshold) < 0.2
                )
                
                vals_ok = (
                    abs(float(current_limit) - expected_limit) < 0.2 and
                    abs(float(total_spent) - expected_spent) < 0.2 and
                    abs(float(remaining_budget) - expected_remaining) < 0.2 and
                    warning_ok and
                    int(entry_count) == expected_entries and
                    isinstance(top_entries, list) and len(top_entries) >= 3
                )
            except Exception:
                vals_ok = False
        
        checks.append({'name': 'summary_json_content', 'passed': bool(has_keys and vals_ok), 'detail': f'has_keys={has_keys}; vals_ok={vals_ok}'})
    except Exception as e:
        checks.append({'name': 'summary_json_content', 'passed': False, 'detail': f'error reading/parsing json: {e}'})

    # Check 5: top 3 entries roughly correct and ordered (flexible key names)
    try:
        data = json.loads(report_json.read_text(encoding='utf-8', errors='replace')) if report_json.exists() else {}
        top_keys = ['top_entries', 'top_3_entries', 'top3_entries', 'top3']
        top_entries = get_value_flexible(data, top_keys, [])
        
        amounts = []
        for item in top_entries[:3]:
            try:
                if isinstance(item, dict):
                    amount_keys = ['amount', 'cost', 'price', 'value']
                    amt = get_value_flexible(item, amount_keys)
                    if amt is not None:
                        amounts.append(float(amt))
                    else:
                        amounts.append(None)
                else:
                    amounts.append(None)
            except Exception:
                amounts.append(None)
        
        ordered = all(amounts[i] is not None and amounts[i] >= amounts[i+1] for i in range(len(amounts)-1)) if len(amounts) >= 2 else True
        correct_top = any(a is not None and abs(a - 6.0) < 0.2 for a in amounts)
        
        checks.append({'name': 'top_entries_order', 'passed': bool(ordered and correct_top), 'detail': f'amounts={amounts}'})
    except Exception as e:
        checks.append({'name': 'top_entries_order', 'passed': False, 'detail': f'error checking top entries: {e}'})

    # Check 6: marker file still present to validate deterministic inputs
    try:
        exists = marker_path.exists()
        marker_ok = False
        detail = 'missing marker file'
        if exists:
            txt = marker_path.read_text(encoding='utf-8', errors='replace')
            marker_ok = ('TOKENGUARD-SEED-2025-04-18' in txt) and ('SESSION-ENTRIES=4' in txt)
            detail = 'marker content verified' if marker_ok else 'marker content mismatch'
        checks.append({'name': 'input_marker', 'passed': bool(exists and marker_ok), 'detail': detail})
    except Exception as e:
        checks.append({'name': 'input_marker', 'passed': False, 'detail': f'error checking marker: {e}'})

    passed_count = sum(1 for c in checks if c.get('passed'))
    total = len(checks) if checks else 1
    result = {
        'passed': passed_count == total,
        'score': passed_count / total,
        'checks': checks
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    try:
        workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    except Exception:
        workspace = '.'
    main(workspace)