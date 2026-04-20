import json
import os
import re
import sys
from pathlib import Path


def load_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None, f"failed to read {path}: {e}"


def normalize(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def has_any(text, phrases):
    nt = normalize(text)
    return any(normalize(p) in nt for p in phrases)


def section_match(text, section_name):
    """Flexible section matching with case-insensitive regex"""
    escaped = re.escape(section_name)
    patterns = [
        rf"(?i)#{1,3}\s*{escaped}\b",  # Markdown headers
        rf"(?i)^\s*{escaped}\s*:",     # Section with colon
        rf"(?i)^\s*{escaped}\s*-$",    # Section with dash
        rf"(?i)\b{escaped}\b",         # Word boundary match
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True
    return False


def check_section_present(text, section_name, synonyms):
    """Check if section or any synonym appears in text"""
    # Check exact section name first
    if section_match(text, section_name):
        return True
    
    # Check all synonyms
    for term in synonyms:
        if section_match(text, term) or has_any(text, [term]):
            return True
    
    # Fallback: check if any synonym appears anywhere in text (case-insensitive)
    nt = normalize(text)
    for term in synonyms:
        if normalize(term) in nt:
            return True
    
    return False


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out_path = workspace / "output.md"

    try:
        exists = out_path.exists()
        checks.append({
            "name": "output file exists",
            "passed": bool(exists),
            "detail": "output.md found" if exists else "output.md is missing"
        })
    except Exception as e:
        checks.append({
            "name": "output file exists",
            "passed": False,
            "detail": f"error checking existence: {e}"
        })

    text = ""
    if out_path.exists():
        try:
            text = out_path.read_text(encoding="utf-8")
            checks.append({
                "name": "non-empty content",
                "passed": len(text.strip()) > 0,
                "detail": f"content length={len(text.strip())}" if text.strip() else "file is empty"
            })
        except Exception as e:
            checks.append({
                "name": "non-empty content",
                "passed": False,
                "detail": f"failed to read output.md: {e}"
            })
    else:
        checks.append({
            "name": "non-empty content",
            "passed": False,
            "detail": "skipped because output.md is missing"
        })

    # Flexible section matching with synonyms
    required_sections = [
        ("Opening", ["opening", "hook", "introduction", "intro", "start", "beginning"]),
        ("Setup", ["setup", "background", "context", "situation", "scenario"]),
        ("The Problem", ["problem", "challenge", "issue", "difficulty", "struggle"]),
        ("Core Concept", ["core", "insight", "key idea", "main point", "concept", "lesson", "takeaway"]),
        ("Real-World Examples", ["example", "examples", "case study", "real world", "practical", "story"]),
        ("Broader Implications", ["implication", "implications", "broader", "impact", "significance", "why it matters"]),
        ("Closing", ["closing", "conclusion", "summary", "wrap up", "ending", "final"]),
        ("Q&A Preparation", ["q&a", "q and a", "questions", "qa preparation", "faq", "anticipated questions"]),
    ]
    try:
        present = []
        missing = []
        for sec_name, synonyms in required_sections:
            found = check_section_present(text, sec_name, synonyms)
            if found:
                present.append(sec_name)
            else:
                missing.append(sec_name)
        checks.append({
            "name": "required sections",
            "passed": len(missing) == 0,
            "detail": f"present={present}; missing={missing}" if missing else f"all sections found: {present}"
        })
    except Exception as e:
        checks.append({
            "name": "required sections",
            "passed": False,
            "detail": f"error while checking sections: {e}"
        })

    try:
        # Check for marker or key concepts from notes
        marker_ok = has_any(text, [
            "TED-TALK-TASK-MARKER-9f3c1a",
            "debugging insight",
            "observability",
            "technical storytelling",
            "deployment failed",
            "migration was delayed",
            "tradeoffs"
        ])
        checks.append({
            "name": "uses provided notes",
            "passed": bool(marker_ok),
            "detail": "references marker or key note concepts" if marker_ok else "does not appear to use the provided notes"
        })
    except Exception as e:
        checks.append({
            "name": "uses provided notes",
            "passed": False,
            "detail": f"error while checking note usage: {e}"
        })

    try:
        word_count = len(re.findall(r"\b\w+\b", text))
        passed = word_count >= 600  # Reduced to 600 for 3-5 minute talk
        checks.append({
            "name": "substantial length",
            "passed": passed,
            "detail": f"word_count={word_count}" if text else "no text available"
        })
    except Exception as e:
        checks.append({
            "name": "substantial length",
            "passed": False,
            "detail": f"error counting words: {e}"
        })

    try:
        qna_ok = has_any(text, [
            "q&a preparation",
            "q and a preparation",
            "common objections",
            "skeptics",
            "questions and responses",
            "anticipated questions",
            "faq",
            "q&a"
        ])
        checks.append({
            "name": "q&a preparation included",
            "passed": bool(qna_ok),
            "detail": "Q&A-style material found" if qna_ok else "Q&A preparation section not detected"
        })
    except Exception as e:
        checks.append({
            "name": "q&a preparation included",
            "passed": False,
            "detail": f"error while checking Q&A: {e}"
        })

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get("passed"))
    score = (passed_count / total) if total else 0.0
    result = {
        "passed": passed_count == total,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal error", "passed": False, "detail": str(e)}]}))