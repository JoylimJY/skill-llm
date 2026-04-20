import json
import os
import re
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def main():
    checks = []
    try:
        workspace = Path(sys.argv[1])
    except Exception as e:
        result = {"passed": False, "score": 0.0, "checks": [{"name": "argument", "passed": False, "detail": f"Invalid workspace argument: {e}"}]}
        print(json.dumps(result))
        return

    story_path = workspace / 'story.md'
    try:
        exists = story_path.exists()
        checks.append({"name": "story_exists", "passed": exists, "detail": "story.md found" if exists else "story.md is missing"})
    except Exception as e:
        checks.append({"name": "story_exists", "passed": False, "detail": f"Error checking file existence: {e}"})

    content = ''
    if story_path.exists():
        try:
            content = story_path.read_text(encoding='utf-8')
            checks.append({"name": "story_readable", "passed": True, "detail": "story.md could be read"})
        except Exception as e:
            checks.append({"name": "story_readable", "passed": False, "detail": f"Could not read story.md: {e}"})
    else:
        checks.append({"name": "story_readable", "passed": False, "detail": "story.md missing, cannot read"})

    norm = normalize(content) if content else ''

    try:
        has_persona = 'marketing manager' in norm
        has_export_pdf = 'export' in norm and 'pdf' in norm
        checks.append({"name": "story_core_text", "passed": bool(has_persona and has_export_pdf), "detail": "Contains marketing manager and export PDF idea" if has_persona and has_export_pdf else "Missing expected story concept"})
    except Exception as e:
        checks.append({"name": "story_core_text", "passed": False, "detail": f"Text validation failed: {e}"})

    try:
        ac_matches = re.findall(r'given|when|then', content, flags=re.IGNORECASE)
        ac_count = len(ac_matches)
        passed = ac_count >= 4
        checks.append({"name": "acceptance_criteria_mentions", "passed": passed, "detail": f"Found {ac_count} Gherkin keywords"})
    except Exception as e:
        checks.append({"name": "acceptance_criteria_mentions", "passed": False, "detail": f"AC parsing failed: {e}"})

    try:
        points_ok = bool(re.search(r'\b3\s*points?\b', norm)) or bool(re.search(r'\bpoints?\s*:?\s*3\b', norm))
        checks.append({"name": "points_3", "passed": points_ok, "detail": "3 story points detected" if points_ok else "3 story points not detected"})
    except Exception as e:
        checks.append({"name": "points_3", "passed": False, "detail": f"Points validation failed: {e}"})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    result = {"passed": passed_count == total and total > 0, "score": score, "checks": checks}
    print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal", "passed": False, "detail": str(e)}]}))
