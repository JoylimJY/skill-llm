import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None


def norm(s):
    if s is None:
        return ''
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


def fuzzy_contains(text, phrases):
    t = norm(text)
    return all(any(p.lower() in t for p in [ph, ph + 's', ph + 'ed', ph + 'ing']) for ph in phrases)


def find_key_by_pattern(data, patterns):
    """Find a key in dict that matches any of the given patterns (case-insensitive, partial match)
    Returns the best matching key based on pattern priority and match quality."""
    if not isinstance(data, dict):
        return None
    
    best_key = None
    best_score = 0
    
    for key in data.keys():
        key_lower = key.lower()
        # Split by underscore to treat as word components
        key_parts = key_lower.split('_')
        
        for pattern in patterns:
            pattern_lower = pattern.lower()
            score = 0
            
            # Check for exact word component match (highest score)
            if pattern_lower in key_parts:
                score = 10
            # Check for word boundary match (treat underscores as boundaries)
            elif re.search(r'[_\s]' + re.escape(pattern_lower) + r'[_\s]', key_lower):
                score = 8
            # Check for substring match (lower score)
            elif pattern_lower in key_lower:
                score = 5
            
            if score > best_score:
                best_score = score
                best_key = key
    
    return best_key


def extract_text_from_value(val):
    """Extract text content from various value types (dict, list, str)"""
    if isinstance(val, str):
        return val
    elif isinstance(val, dict):
        return ' '.join(str(v) for v in val.values())
    elif isinstance(val, list):
        return ' '.join(extract_text_from_value(item) for item in val)
    else:
        return str(val)


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    # Check 1: output file exists and is non-empty
    try:
        out_txt = workspace / 'output' / 'summary.txt'
        if out_txt.exists():
            content = out_txt.read_text(encoding='utf-8')
            passed = len(content.strip()) > 0
            detail = 'summary.txt exists and is non-empty' if passed else 'summary.txt is empty'
        else:
            passed = False
            detail = 'summary.txt is missing'
    except Exception as e:
        passed = False
        detail = f'error reading summary.txt: {e}'
    checks.append({'name': 'summary_txt_exists', 'passed': passed, 'detail': detail})

    # Check 2: summary mentions key files and duplication guidance
    try:
        content = (workspace / 'output' / 'summary.txt').read_text(encoding='utf-8') if (workspace / 'output' / 'summary.txt').exists() else ''
        phrases = ['readme', 'spec', 'duplicate', 'token', 'first']
        passed = fuzzy_contains(content, phrases)
        detail = 'mentions README/spec/duplicate/token/first' if passed else 'missing one or more key concepts'
    except Exception as e:
        passed = False
        detail = f'could not evaluate summary text: {e}'
    checks.append({'name': 'summary_content', 'passed': passed, 'detail': detail})

    # Check 3: JSON output exists and has expected content (fuzzy key matching)
    try:
        out_json = workspace / 'output' / 'summary.json'
        if not out_json.exists():
            passed = False
            detail = 'summary.json is missing'
        else:
            data = json.loads(out_json.read_text(encoding='utf-8'))
            
            # Fuzzy match for important files key - check 'important' BEFORE 'priority' to avoid matching low_priority_files
            imp_key = find_key_by_pattern(data, ['important', 'main', 'key', 'priority'])
            # Fuzzy match for redundancy/duplicates key
            dup_key = find_key_by_pattern(data, ['duplicate', 'redundant', 'repeats', 'redundancy'])
            # Fuzzy match for reading order/recommendation key
            rec_key = find_key_by_pattern(data, ['recommend', 'order', 'read', 'first', 'priority'])
            
            if imp_key and dup_key and rec_key:
                # Extract text content from potentially nested structures
                imp_text = extract_text_from_value(data.get(imp_key, []))
                dup_text = extract_text_from_value(data.get(dup_key, []))
                rec_text = extract_text_from_value(data.get(rec_key, ''))
                
                # Check important files mention readme and spec
                imp_ok = fuzzy_contains(imp_text, ['readme', 'spec'])
                # Check duplicates mention redundancy
                dup_ok = fuzzy_contains(dup_text, ['duplicate', 'repeat', 'redundant'])
                # Check reading order has file paths (contains at least one path-like string)
                rec_ok = len(rec_text.strip()) > 0 and ('/' in rec_text or 'readme' in norm(rec_text) or 'spec' in norm(rec_text))
                
                passed = imp_ok and dup_ok and rec_ok
                detail = 'summary.json contains required fields with expected high-level content' if passed else 'summary.json content did not match expectations'
            else:
                missing = []
                if not imp_key:
                    missing.append('important_files (or similar)')
                if not dup_key:
                    missing.append('redundant_or_duplicate_info (or similar)')
                if not rec_key:
                    missing.append('read_first_recommendation (or similar)')
                passed = False
                detail = f'missing required keys: {missing}'
    except Exception as e:
        passed = False
        detail = f'error parsing summary.json: {e}'
    checks.append({'name': 'summary_json_schema', 'passed': passed, 'detail': detail})

    # Check 4: JSON mirrors text with marker of concision
    try:
        txt = (workspace / 'output' / 'summary.txt').read_text(encoding='utf-8') if (workspace / 'output' / 'summary.txt').exists() else ''
        js = json.loads((workspace / 'output' / 'summary.json').read_text(encoding='utf-8')) if (workspace / 'output' / 'summary.json').exists() else {}
        txt_words = len(norm(txt).split())
        js_ok = isinstance(js, dict) and bool(js)
        passed = js_ok and txt_words > 0 and txt_words < 250
        detail = f'text length={txt_words} words; json present={js_ok}' if passed else 'summary too long or json missing'
    except Exception as e:
        passed = False
        detail = f'error comparing outputs: {e}'
    checks.append({'name': 'concise_output', 'passed': passed, 'detail': detail})

    score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
    result = {'passed': all(c['passed'] for c in checks), 'score': score, 'checks': checks}
    print(json.dumps(result))


if __name__ == '__main__':
    main()