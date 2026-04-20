import json
import re
from pathlib import Path


def normalize(text):
    text = text.lower()
    text = re.sub(r'[^\w\s\.\-]', ' ', text, flags=re.UNICODE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def main(workspace_dir):
    checks = []
    try:
        ws = Path(workspace_dir)
    except Exception as e:
        result = {"passed": False, "score": 0.0, "checks": [{"name": "workspace_path", "passed": False, "detail": f"invalid workspace path: {e}"}]}
        print(json.dumps(result, ensure_ascii=False))
        return

    # Check 1: output file exists
    try:
        birthdays = ws / 'data' / 'birthdays.md'
        exists = birthdays.exists()
        checks.append({"name": "output_file_exists", "passed": exists, "detail": "found" if exists else "missing data/birthdays.md"})
    except Exception as e:
        checks.append({"name": "output_file_exists", "passed": False, "detail": f"error checking file existence: {e}"})

    # Check 2: content contains Valentina entry
    try:
        content = birthdays.read_text(encoding='utf-8') if birthdays.exists() else ''
        n = normalize(content)
        has_name = 'valentina' in n
        has_date = '14.02.2000' in content or '14.02.2000' in n or '14.02' in n
        passed = has_name and has_date
        checks.append({"name": "valentina_entry_present", "passed": passed, "detail": f"name={has_name}, date={has_date}"})
    except Exception as e:
        checks.append({"name": "valentina_entry_present", "passed": False, "detail": f"error reading content: {e}"})

    # Check 3: turning age mentioned somewhere for Valentina
    try:
        content = birthdays.read_text(encoding='utf-8') if birthdays.exists() else ''
        n = normalize(content)
        # Accept either explicit age or a plausible turning-age note
        age_match = bool(re.search(r'\b(wird|turning)\b\s*\d+', n)) or 'wird 26' in n or 'turning 26' in n
        checks.append({"name": "turning_age_mentioned", "passed": age_match, "detail": "age note found" if age_match else "no turning-age note detected"})
    except Exception as e:
        checks.append({"name": "turning_age_mentioned", "passed": False, "detail": f"error parsing age note: {e}"})

    # Check 4: marker file preserved/created
    try:
        marker = ws / 'marker.txt'
        ok = marker.exists() and 'MARKER_BIRTHDAY_INPUT_V1' in marker.read_text(encoding='utf-8', errors='ignore')
        checks.append({"name": "marker_file", "passed": ok, "detail": "marker present" if ok else "marker missing or altered"})
    except Exception as e:
        checks.append({"name": "marker_file", "passed": False, "detail": f"error checking marker: {e}"})

    passed_count = sum(1 for c in checks if c.get('passed'))
    total = len(checks)
    score = passed_count / total if total else 0.0
    result = {"passed": passed_count == total and total > 0, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
