import json
import os
import re
import sys
from pathlib import Path


def normalize(s):
    try:
        s = s.lower()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"[\W_]+", "", s)
        return s
    except Exception:
        return ""


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    try:
        out_path = workspace / "cleaned.txt"
        if not out_path.exists():
            add_check("output_exists", False, "cleaned.txt is missing")
            text = ""
        else:
            try:
                text = out_path.read_text(encoding="utf-8", errors="replace")
                add_check("output_exists", True, "cleaned.txt found")
            except Exception as e:
                text = ""
                add_check("output_exists", False, f"Could not read cleaned.txt: {e}")

        try:
            has_hedge = bool(re.search(r"at the end of the day|it is important to remember|it's worth noting", text, re.I))
            passed = not has_hedge and bool(text.strip())
            add_check("remove_hedging", passed, "Found hedging phrase" if has_hedge else "No obvious hedging phrase found")
        except Exception as e:
            add_check("remove_hedging", False, f"Regex check failed: {e}")

        try:
            has_stock = bool(re.search(r"\b(first|secondly|finally)\b", text, re.I))
            passed = not has_stock and bool(text.strip())
            add_check("remove_stock_transitions", passed, "Found stock transition" if has_stock else "No stock transition found")
        except Exception as e:
            add_check("remove_stock_transitions", False, f"Regex check failed: {e}")

        try:
            sig_phrase = normalize("I hope this helps")
            found = sig_phrase in normalize(text)
            passed = not found and bool(text.strip())
            add_check("remove_authenticity_cue", passed, "Found closing phrase" if found else "No closing phrase found")
        except Exception as e:
            add_check("remove_authenticity_cue", False, f"Normalization failed: {e}")

        try:
            marker_path = workspace / "marker.txt"
            marker_ok = marker_path.exists() and "HUMANIZER_MARKER_42" in marker_path.read_text(encoding="utf-8", errors="replace")
            add_check("input_marker_present", marker_ok, "Marker present" if marker_ok else "Marker missing or unreadable")
        except Exception as e:
            add_check("input_marker_present", False, f"Marker check failed: {e}")

    except Exception as e:
        add_check("fatal_error", False, f"Unexpected grader error: {e}")

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    result = {
        "passed": passed_count == total and total > 0,
        "score": (passed_count / total) if total else 0.0,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
