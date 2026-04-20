import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1])

    # Check 1: input fixture exists and contains marker
    try:
        input_path = workspace / 'batch_input.json'
        if not input_path.exists():
            checks.append({"name": "input_fixture_exists", "passed": False, "detail": "batch_input.json is missing"})
            data = None
        else:
            try:
                data = json.loads(input_path.read_text(encoding='utf-8'))
                marker_ok = 'marker' in data and 'near_batch_task_marker_v1' in str(data.get('marker', '')).lower().replace('_', '')
                checks.append({"name": "input_fixture_marker", "passed": bool(marker_ok), "detail": f"marker={'found' if marker_ok else 'not found'}"})
            except Exception as e:
                checks.append({"name": "input_fixture_marker", "passed": False, "detail": f"could not parse batch_input.json: {e}"})
                data = None
    except Exception as e:
        checks.append({"name": "input_fixture_exists", "passed": False, "detail": f"error checking input fixture: {e}"})
        data = None

    # Check 2: output estimate file exists
    try:
        out_path = workspace / 'output.txt'
        if not out_path.exists():
            checks.append({"name": "output_file_exists", "passed": False, "detail": "output.txt is missing"})
            out_text = None
        else:
            out_text = out_path.read_text(encoding='utf-8', errors='replace')
            checks.append({"name": "output_file_exists", "passed": True, "detail": "output.txt found"})
    except Exception as e:
        checks.append({"name": "output_file_exists", "passed": False, "detail": f"error reading output.txt: {e}"})
        out_text = None

    # Check 3: estimate text mentions NEAR and gas/cost terminology with fuzzy matching
    try:
        if out_text is None:
            checks.append({"name": "output_mentions_estimate", "passed": False, "detail": "no readable output text"})
        else:
            normalized = re.sub(r'[^a-z0-9]+', ' ', out_text.lower())
            terms = ["near", "gas", "estimate"]
            passed = all(term in normalized for term in terms)
            checks.append({"name": "output_mentions_estimate", "passed": passed, "detail": f"terms_present={passed}"})
    except Exception as e:
        checks.append({"name": "output_mentions_estimate", "passed": False, "detail": f"exception during text check: {e}"})

    # Check 4: output includes a numeric estimate-like value
    try:
        if out_text is None:
            checks.append({"name": "output_has_numeric_estimate", "passed": False, "detail": "no readable output text"})
        else:
            nums = re.findall(r'\d+(?:\.\d+)?', out_text)
            passed = len(nums) >= 1
            checks.append({"name": "output_has_numeric_estimate", "passed": passed, "detail": f"found_numbers={nums[:5]}"})
    except Exception as e:
        checks.append({"name": "output_has_numeric_estimate", "passed": False, "detail": f"exception during numeric scan: {e}"})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    result = {"passed": passed_count == total and total > 0, "score": (passed_count / total) if total else 0.0, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal_error", "passed": False, "detail": str(e)}]}, ensure_ascii=False))
