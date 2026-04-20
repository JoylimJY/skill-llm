import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else Path('.')
checks = []

try:
    expected_path = workspace / 'expected-triage.json'
    inbox_path = workspace / 'gmail-inbox-summaries.json'
    triage_path = workspace / 'gmail-triage-labels.json'
    digest_path = workspace / 'gmail-triage.md'

    expected = json.loads(expected_path.read_text(encoding='utf-8')) if expected_path.exists() else []
    inbox = json.loads(inbox_path.read_text(encoding='utf-8')) if inbox_path.exists() else []
except Exception as e:
    expected = []
    inbox = []
    checks.append({"name": "load_inputs", "passed": False, "detail": f"Could not load input files: {type(e).__name__}: {e}"})

# Check 1: inbox input exists and contains marker content
try:
    ok = bool(inbox) and any('GM-TRIAGE-MARKER-7F3A' in (item.get('snippet','') or '') for item in inbox if isinstance(item, dict))
    detail = f"Loaded {len(inbox)} inbox items with marker present." if ok else "Missing inbox file or marker content."
    checks.append({"name": "input_marker", "passed": ok, "detail": detail})
except Exception as e:
    checks.append({"name": "input_marker", "passed": False, "detail": f"Error checking inbox marker: {type(e).__name__}: {e}"})

# Check 2: triage labels file exists
try:
    ok = triage_path.exists()
    checks.append({"name": "triage_labels_exists", "passed": ok, "detail": "gmail-triage-labels.json present." if ok else "gmail-triage-labels.json is missing."})
except Exception as e:
    checks.append({"name": "triage_labels_exists", "passed": False, "detail": f"Error: {type(e).__name__}: {e}"})

# Check 3: triage labels content matches expected by threadId, forgiving on ordering and extra fields
try:
    passed = False
    detail = ""
    if triage_path.exists():
        actual = json.loads(triage_path.read_text(encoding='utf-8'))
        if isinstance(actual, dict):
            actual = actual.get('items') or actual.get('labels') or []
        if not isinstance(actual, list):
            actual = []
        exp_map = {item.get('threadId'): item for item in expected if isinstance(item, dict) and item.get('threadId')}
        act_map = {item.get('threadId'): item for item in actual if isinstance(item, dict) and item.get('threadId')}
        matched = 0
        total = len(exp_map)
        missing = []
        bad = []
        for tid, exp in exp_map.items():
            act = act_map.get(tid)
            if not act:
                missing.append(tid)
                continue
            exp_labels = set([str(x).strip().lower() for x in exp.get('labels', []) if x])
            act_labels = set([str(x).strip().lower() for x in (act.get('labels') or ([act.get('label')] if act.get('label') else [])) if x])
            # needsReply may be represented in either boolean or action field
            exp_nr = bool(exp.get('needsReply'))
            act_nr = bool(act.get('needsReply')) or str(act.get('action','')).strip().lower() == 'reply'
            if exp_labels.issubset(act_labels) and exp_nr == act_nr:
                matched += 1
            else:
                bad.append(tid)
        passed = (matched == total)
        detail = f"Matched {matched}/{total}. Missing: {missing[:3]}. Mismatched: {bad[:3]}."
    else:
        detail = "gmail-triage-labels.json missing."
    checks.append({"name": "triage_labels_content", "passed": passed, "detail": detail})
except Exception as e:
    checks.append({"name": "triage_labels_content", "passed": False, "detail": f"Error validating labels: {type(e).__name__}: {e}"})

# Check 4: triage digest exists and mentions at least one high-priority category
try:
    passed = False
    if digest_path.exists():
        txt = digest_path.read_text(encoding='utf-8', errors='ignore')
        norm = ''.join(ch.lower() for ch in txt if ch.isalnum() or ch.isspace())
        keywords = ['urgent', 'needs reply', 'admin', 'mayo', 'school']
        passed = any(k in norm for k in keywords)
        detail = "Digest mentions priority categories." if passed else "Digest does not mention expected categories."
    else:
        detail = "gmail-triage.md missing."
    checks.append({"name": "triage_digest", "passed": passed, "detail": detail})
except Exception as e:
    checks.append({"name": "triage_digest", "passed": False, "detail": f"Error checking digest: {type(e).__name__}: {e}"})

# Check 5: overall file completeness
try:
    required = [triage_path, digest_path]
    passed = all(p.exists() for p in required)
    detail = 'All required output files present.' if passed else 'One or more required output files are missing.'
    checks.append({"name": "required_outputs", "passed": passed, "detail": detail})
except Exception as e:
    checks.append({"name": "required_outputs", "passed": False, "detail": f"Error: {type(e).__name__}: {e}"})

try:
    score = sum(1 for c in checks if c.get('passed')) / max(1, len(checks))
    passed = all(c.get('passed') for c in checks)
    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "finalize", "passed": False, "detail": f"Failed to finalize results: {type(e).__name__}: {e}"}]}))
