import json
import os
import re
import sys
from pathlib import Path


def normalize(s):
    try:
        s = s.lower()
        s = re.sub(r'[^a-z0-9]+', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s
    except Exception:
        return ''


def read_text_file(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def check_section(content, patterns):
    """Check if content matches any of the given patterns (case-insensitive)."""
    norm = normalize(content)
    for pattern in patterns:
        if re.search(pattern, norm, re.IGNORECASE):
            return True
    return False


def main():
    checks = []
    try:
        ws = Path(sys.argv[1])
    except Exception as e:
        result = {"passed": False, "score": 0.0, "checks": [{"name": "workspace arg", "passed": False, "detail": f"invalid workspace argument: {e}"}]}
        print(json.dumps(result))
        return

    output_path = ws / 'output.txt'
    passed = output_path.exists()
    detail = 'output.txt exists' if passed else 'output.txt is missing'
    checks.append({"name": "output file exists", "passed": passed, "detail": detail})

    content = ''
    if passed:
        try:
            content = output_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            checks.append({"name": "output readable", "passed": False, "detail": f"could not read output.txt: {e}"})
            content = ''
        else:
            checks.append({"name": "output readable", "passed": True, "detail": "output.txt could be read"})
    else:
        checks.append({"name": "output readable", "passed": False, "detail": "skipped because output.txt is missing"})

    # Check for opening/hook section
    opening_patterns = [
        r'opening', r'hook', r'introduction', r'start', r'begin', r'intro'
    ]
    ok = check_section(content, opening_patterns)
    checks.append({"name": "contains section opening", "passed": ok, "detail": f"section {'found' if ok else 'not found'}"})

    # Check for problem/challenge section
    problem_patterns = [
        r'problem', r'challenge', r'issue', r'pain', r'why this matters', r'motivation', r'background'
    ]
    ok = check_section(content, problem_patterns)
    checks.append({"name": "contains section problem", "passed": ok, "detail": f"section {'found' if ok else 'not found'}"})

    # Check for core concept/explanation section
    concept_patterns = [
        r'core', r'concept', r'idea', r'insight', r'explanation', r'how it works', r'main', r'key'
    ]
    ok = check_section(content, concept_patterns)
    checks.append({"name": "contains section core concept", "passed": ok, "detail": f"section {'found' if ok else 'not found'}"})

    # Check for examples section
    example_patterns = [
        r'example', r'case study', r'demonstration', r'illustration', r'scenario', r'concrete', r'practical'
    ]
    ok = check_section(content, example_patterns)
    checks.append({"name": "contains section examples", "passed": ok, "detail": f"section {'found' if ok else 'not found'}"})

    # Check for implications section
    implication_patterns = [
        r'implication', r'impact', r'consequence', r'broader', r'future', r'what this means', r'takeaway'
    ]
    ok = check_section(content, implication_patterns)
    checks.append({"name": "contains section implications", "passed": ok, "detail": f"section {'found' if ok else 'not found'}"})

    # Check for closing section
    closing_patterns = [
        r'closing', r'conclusion', r'summary', r'wrap', r'end', r'final', r'thank'
    ]
    ok = check_section(content, closing_patterns)
    checks.append({"name": "contains section closing", "passed": ok, "detail": f"section {'found' if ok else 'not found'}"})

    # Check for Q&A section
    qa_patterns = [
        r'q&a', r'q a', r'questions', r'answers', r'faq', r'audience', r'discussion'
    ]
    ok = check_section(content, qa_patterns)
    checks.append({"name": "contains section q&a", "passed": ok, "detail": f"section {'found' if ok else 'not found'}"})

    # Check for source markers from input notes
    marker_ok = False
    try:
        norm = normalize(content)
        marker_ok = ('bootstrap observability' in norm) or ('learn normal before enforcing alerts' in norm)
    except Exception:
        marker_ok = False
    checks.append({"name": "includes source markers", "passed": marker_ok, "detail": "found marker-related topic text" if marker_ok else "missing marker-related topic text"})

    # Check for sufficient length
    length_ok = False
    try:
        word_count = len(re.findall(r'\w+', content))
        length_ok = word_count >= 150
        checks.append({"name": "sufficient length", "passed": length_ok, "detail": f"word count={word_count}"})
    except Exception as e:
        checks.append({"name": "sufficient length", "passed": False, "detail": f"could not count words: {e}"})

    total = len(checks)
    passed_checks = sum(1 for c in checks if c.get('passed'))
    score = (passed_checks / total) if total else 0.0
    overall = all(c.get('passed') for c in checks)
    result = {"passed": overall, "score": score, "checks": checks}
    print(json.dumps(result))


if __name__ == '__main__':
    main()