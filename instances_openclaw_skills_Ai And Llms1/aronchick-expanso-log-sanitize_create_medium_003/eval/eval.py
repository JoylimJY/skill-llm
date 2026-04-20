import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []

try:
    expected_files = ["app.log.sanitized", "auth.log.sanitized", "audit.txt.sanitized", "summary.txt"]
    present = []
    missing = []
    for fname in expected_files:
        if (workspace / fname).exists():
            present.append(fname)
        else:
            missing.append(fname)
    checks.append({
        "name": "expected_files_exist",
        "passed": len(missing) == 0,
        "detail": f"present={present}; missing={missing}"
    })
except Exception as e:
    checks.append({"name": "expected_files_exist", "passed": False, "detail": f"error: {type(e).__name__}: {e}"})

patterns = [
    r"password\s*[:=]\s*\S+",
    r"api[_-]?token\s*[:=]\s*\S+",
    r"bearer\s+eyJ[A-Za-z0-9_\-\.]+",
    r"session[_-]?id\s*[:=]\s*\S+",
    r"secret[_-]?key\s*[:=]\s*\S+",
]

try:
    sanitized_ok = True
    details = []
    for fname in ["app.log.sanitized", "auth.log.sanitized", "audit.txt.sanitized"]:
        try:
            text = (workspace / fname).read_text(encoding="utf-8", errors="replace")
            lower = text.lower()
            hits = []
            for pat in patterns:
                try:
                    if re.search(pat, lower, flags=re.IGNORECASE):
                        hits.append(pat)
                except Exception:
                    continue
            ok = len(hits) == 0
            sanitized_ok = sanitized_ok and ok
            details.append(f"{fname}: remaining_sensitive_patterns={hits}")
        except Exception as e:
            sanitized_ok = False
            details.append(f"{fname}: error {type(e).__name__}: {e}")
    checks.append({
        "name": "sensitive_content_removed",
        "passed": sanitized_ok,
        "detail": " | ".join(details)
    })
except Exception as e:
    checks.append({"name": "sensitive_content_removed", "passed": False, "detail": f"error: {type(e).__name__}: {e}"})

try:
    summary_path = workspace / "summary.txt"
    summary_text = summary_path.read_text(encoding="utf-8", errors="replace") if summary_path.exists() else ""
    expected_terms = ["app.log", "auth.log", "audit.txt"]
    all_listed = all(term.lower() in summary_text.lower() for term in expected_terms)
    checks.append({
        "name": "summary_mentions_all_files",
        "passed": all_listed,
        "detail": f"contains_terms={expected_terms}"
    })
except Exception as e:
    checks.append({"name": "summary_mentions_all_files", "passed": False, "detail": f"error: {type(e).__name__}: {e}"})

try:
    counts_ok = True
    count_details = []
    summary_text = (workspace / "summary.txt").read_text(encoding="utf-8", errors="replace") if (workspace / "summary.txt").exists() else ""
    for fname in ["app.log", "auth.log", "audit.txt"]:
        sanitized_name = f"{fname}.sanitized"
        if not (workspace / sanitized_name).exists():
            counts_ok = False
            count_details.append(f"{sanitized_name}: missing")
            continue
        orig = (workspace / fname).read_text(encoding="utf-8", errors="replace") if (workspace / fname).exists() else ""
        new = (workspace / sanitized_name).read_text(encoding="utf-8", errors="replace")
        orig_hits = 0
        new_hits = 0
        for pat in patterns:
            try:
                orig_hits += len(re.findall(pat, orig, flags=re.IGNORECASE))
                new_hits += len(re.findall(pat, new, flags=re.IGNORECASE))
            except Exception:
                pass
        if new_hits > 0:
            counts_ok = False
        if fname.lower() not in summary_text.lower():
            counts_ok = False
        count_details.append(f"{fname}: orig_hits={orig_hits}, new_hits={new_hits}")
    checks.append({
        "name": "summary_and_counts_reasonable",
        "passed": counts_ok,
        "detail": " | ".join(count_details)
    })
except Exception as e:
    checks.append({"name": "summary_and_counts_reasonable", "passed": False, "detail": f"error: {type(e).__name__}: {e}"})

try:
    total = len(checks)
    passed = sum(1 for c in checks if c.get("passed"))
    score = passed / total if total else 0.0
    result = {"passed": passed == total, "score": score, "checks": checks}
    print(json.dumps(result))
except Exception:
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
