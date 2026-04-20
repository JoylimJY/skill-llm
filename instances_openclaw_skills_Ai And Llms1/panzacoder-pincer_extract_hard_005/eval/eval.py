import json
import os
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return ''.join(ch.lower() for ch in str(s) if ch.isalnum())
    except Exception:
        return ''


workspace = Path(os.environ.get('WORKSPACE_DIR', '.') if len(os.sys.argv) < 2 else os.sys.argv[1])
checks = []

try:
    out_path = workspace / 'output.json'
    if not out_path.exists():
        checks.append({"name": "output_exists", "passed": False, "detail": "output.json is missing"})
        data = None
    else:
        try:
            data = json.loads(out_path.read_text(encoding='utf-8'))
            checks.append({"name": "output_exists", "passed": True, "detail": "output.json found and parsed"})
        except Exception as e:
            data = None
            checks.append({"name": "output_exists", "passed": False, "detail": f"output.json exists but could not be parsed: {e}"})
except Exception as e:
    data = None
    checks.append({"name": "output_exists", "passed": False, "detail": f"unexpected error checking output.json: {e}"})

try:
    if isinstance(data, dict):
        rl = str(data.get('risk_level', ''))
        ok = 'danger' in normalize(rl)
        checks.append({"name": "risk_level", "passed": ok, "detail": f"risk_level={rl!r}"})
    else:
        checks.append({"name": "risk_level", "passed": False, "detail": "output is not a JSON object"})
except Exception as e:
    checks.append({"name": "risk_level", "passed": False, "detail": f"error reading risk_level: {e}"})

try:
    if isinstance(data, dict):
        blocked = data.get('blocked_items', [])
        expected = ["sketchy-tool", "old-malware-skill"]
        nblocked = [normalize(x) for x in blocked] if isinstance(blocked, list) else []
        ok = all(any(normalize(exp) == item for item in nblocked) for exp in expected)
        checks.append({"name": "blocked_items", "passed": ok, "detail": f"blocked_items={blocked!r}"})
    else:
        checks.append({"name": "blocked_items", "passed": False, "detail": "missing JSON object"})
except Exception as e:
    checks.append({"name": "blocked_items", "passed": False, "detail": f"error checking blocked_items: {e}"})

try:
    if isinstance(data, dict):
        pubs = data.get('trusted_publishers', [])
        expected = ["openclaw", "steipete", "invariantlabs-ai"]
        npubs = [normalize(x) for x in pubs] if isinstance(pubs, list) else []
        ok = all(any(normalize(exp) == item for item in npubs) for exp in expected)
        checks.append({"name": "trusted_publishers", "passed": ok, "detail": f"trusted_publishers={pubs!r}"})
    else:
        checks.append({"name": "trusted_publishers", "passed": False, "detail": "missing JSON object"})
except Exception as e:
    checks.append({"name": "trusted_publishers", "passed": False, "detail": f"error checking trusted_publishers: {e}"})

try:
    if isinstance(data, dict):
        warnings = data.get('warnings', [])
        text = ' | '.join(str(x) for x in warnings) if isinstance(warnings, list) else str(warnings)
        norm = normalize(text)
        ok = ('curlwgetpipedtoshelldetected' in norm) and ('externalurlfound' in norm) and ('xattrdquarantine' in norm)
        checks.append({"name": "warnings", "passed": ok, "detail": f"warnings={warnings!r}"})
    else:
        checks.append({"name": "warnings", "passed": False, "detail": "missing JSON object"})
except Exception as e:
    checks.append({"name": "warnings", "passed": False, "detail": f"error checking warnings: {e}"})

try:
    score = sum(1 for c in checks if c.get('passed')) / len(checks) if checks else 0.0
    passed = all(c.get('passed') for c in checks) if checks else False
except Exception:
    score = 0.0
    passed = False

print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
