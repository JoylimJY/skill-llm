import json
import os
import re
import sys
from pathlib import Path

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

try:
    release = (workspace / "press_release.txt").read_text(encoding="utf-8")
    ok = all(k in release.lower() for k in ["northstar one", "14-day free trial", "weekly summaries"])
    add_check("press release exists and includes key facts", ok, "Found required product details." if ok else "Missing one or more required details.")
except Exception as e:
    add_check("press release exists and includes key facts", False, f"Could not read press_release.txt: {e}")

try:
    thread = (workspace / "social_thread.txt").read_text(encoding="utf-8")
    tweets = [t for t in re.split(r"\n\s*\n", thread.strip()) if t.strip()]
    ok = len(tweets) >= 5
    add_check("social thread has at least 5 tweet blocks", ok, f"Found {len(tweets)} tweet blocks." if tweets else "No tweet blocks found.")
except Exception as e:
    add_check("social thread has at least 5 tweet blocks", False, f"Could not read social_thread.txt: {e}")

try:
    faq = (workspace / "faq.txt").read_text(encoding="utf-8")
    phrase_ok = "built for teams that move fast without losing clarity" in faq.lower()
    qmark_ok = faq.count("?") >= 3
    ok = phrase_ok and qmark_ok
    add_check("faq contains required phrase and multiple questions", ok, "FAQ includes the required phrase and question format." if ok else "Missing required phrase or too few questions.")
except Exception as e:
    add_check("faq contains required phrase and multiple questions", False, f"Could not read faq.txt: {e}")

passed = all(c["passed"] for c in checks)
score = sum(1 for c in checks if c["passed"]) / len(checks) if checks else 0.0
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
