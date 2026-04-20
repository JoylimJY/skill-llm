import json
import os
import re
from pathlib import Path


def norm(text):
    text = text.lower()
    text = re.sub(r"[\W_]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def find_file(workspace, candidates):
    for name in candidates:
        p = Path(workspace) / name
        if p.exists():
            return p
    return None


def read_text_safe(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None, str(e)


def main():
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    checks = []

    try:
        target = find_file(workspace, ["talk.md", "output.md", "response.md", "output.txt", "ted_talk.md"])
        if target is None:
            checks.append({"name": "output file exists", "passed": False, "detail": "No expected output file found (looked for talk.md, output.md, response.md, output.txt, ted_talk.md)."})
            content = ""
        else:
            try:
                content = target.read_text(encoding="utf-8")
                checks.append({"name": "output file exists", "passed": True, "detail": f"Found {target.name}."})
            except Exception as e:
                content = ""
                checks.append({"name": "output file exists", "passed": False, "detail": f"Could not read {target.name}: {e}"})
    except Exception as e:
        content = ""
        checks.append({"name": "output file exists", "passed": False, "detail": f"Unexpected error locating output: {e}"})

    try:
        n = norm(content)
        # More flexible section detection with fuzzy matching
        section_patterns = [
            r"opening|hook|intro|introduction",
            r"setup|background|context",
            r"problem|challenge|issue|pain",
            r"core|concept|idea|insight|key",
            r"example|case|story|scenario",
            r"implication|impact|broader|future",
            r"closing|conclusion|summary|wrap",
            r"q\s*a|question|faq|objection"
        ]
        found = [i for i, pattern in enumerate(section_patterns) if re.search(pattern, n)]
        passed = len(found) >= 5  # Require at least 5 of 8 sections
        checks.append({"name": "required sections present", "passed": passed, "detail": f"Found {len(found)}/8 sections."})
    except Exception as e:
        checks.append({"name": "required sections present", "passed": False, "detail": f"Section scan failed: {e}"})

    try:
        n = norm(content)
        hooks = ["3 am", "pager", "debugging", "problem", "pain", "why this matters", "phone call", "incident"]
        passed = any(h in n for h in hooks)
        checks.append({"name": "hook with problem", "passed": passed, "detail": "Talk appears to start with a relatable technical pain point." if passed else "Could not detect a strong problem-based hook."})
    except Exception as e:
        checks.append({"name": "hook with problem", "passed": False, "detail": f"Hook scan failed: {e}"})

    try:
        n = norm(content)
        markers = ["bootstrap", "learn", "enforce", "normal", "threshold", "observability", "baseline"]
        passed = sum(1 for m in markers if m in n) >= 3
        checks.append({"name": "core insight grounded", "passed": passed, "detail": "Core technical idea is reflected with key terms and progression." if passed else "Missing enough evidence of the bootstrap/learn/enforce insight."})
    except Exception as e:
        checks.append({"name": "core insight grounded", "passed": False, "detail": f"Core insight scan failed: {e}"})

    try:
        n = norm(content)
        qterms = ["q a", "q and a", "question", "faq", "objection", "common", "how long", "small project"]
        passed = any(t in n for t in qterms)
        checks.append({"name": "q&a prep included", "passed": passed, "detail": "Q&A or objection-handling content detected." if passed else "No clear Q&A preparation found."})
    except Exception as e:
        checks.append({"name": "q&a prep included", "passed": False, "detail": f"Q&A scan failed: {e}"})

    try:
        n = norm(content)
        concrete = ["3 am", "7 14 days", "week", "production", "dashboard", "logs", "metrics", "trace", "alert", "incident"]
        passed = sum(1 for c in concrete if c in n) >= 3  # Reduced threshold
        checks.append({"name": "concrete examples present", "passed": passed, "detail": "Concrete, specific details appear in the talk." if passed else "Too few concrete details detected."})
    except Exception as e:
        checks.append({"name": "concrete examples present", "passed": False, "detail": f"Concrete example scan failed: {e}"})

    try:
        score = sum(1 for c in checks if c.get("passed")) / len(checks) if checks else 0.0
        passed = score >= 0.6  # Reduced threshold from 0.8
    except Exception:
        score = 0.0
        passed = False

    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()