import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8', errors='replace'), None
    except Exception as e:
        return None, str(e)


try:
    output_path = workspace / "sanitized.log"
    input_path = workspace / "input.log"

    if not input_path.exists():
        add_check("input exists", False, "input.log is missing")
    else:
        add_check("input exists", True, "input.log found")

    if not output_path.exists():
        add_check("output exists", False, "sanitized.log is missing")
        output_text = None
    else:
        output_text, err = safe_read(output_path)
        if output_text is None:
            add_check("output readable", False, f"could not read sanitized.log: {err}")
        else:
            add_check("output readable", True, "sanitized.log read successfully")

    if input_path.exists() and output_path.exists():
        try:
            input_text = input_path.read_text(encoding='utf-8', errors='replace')
            output_text = output_text if output_text is not None else output_path.read_text(encoding='utf-8', errors='replace')

            sensitive_patterns = [
                r'password\s*[:=]\s*\S+',
                r'bearer\s+token\s*[:=]?\s*\S+',
                r'api[_-]?key\s*[:=]\s*\S+',
                r'session[_-]?id\s*[:=]\s*\S+',
            ]
            found_any = False
            for pat in sensitive_patterns:
                if re.search(pat, input_text, flags=re.IGNORECASE):
                    found_any = True
                    break

            if found_any:
                redacted = True
                for pat in sensitive_patterns:
                    matches = re.findall(pat, input_text, flags=re.IGNORECASE)
                    for m in matches:
                        token = re.sub(r'[^a-zA-Z0-9]+', '', m).lower()
                        if token and token in re.sub(r'[^a-zA-Z0-9]+', '', output_text).lower():
                            redacted = False
                            break
                    if not redacted:
                        break
                add_check("sensitive data removed", redacted, "sensitive markers appear to be removed from output")
            else:
                add_check("sensitive data removed", True, "no sensitive patterns found in input")

            marker_ok = "user login succeeded for alice" in output_text.lower() and "request completed successfully" in output_text.lower()
            add_check("non-sensitive content preserved", marker_ok, "expected non-sensitive log lines are present")

            lines_in = [ln for ln in input_text.splitlines() if ln.strip()]
            lines_out = [ln for ln in output_text.splitlines() if ln.strip()]
            length_ok = len(lines_out) > 0 and len(lines_out) <= len(lines_in)
            add_check("output structure reasonable", length_ok, f"input lines={len(lines_in)}, output lines={len(lines_out)}")
        except Exception as e:
            add_check("content checks", False, f"failed to compare files: {e}")

except Exception as e:
    add_check("unexpected error", False, str(e))

passed = all(c["passed"] for c in checks) if checks else False
score = (sum(1 for c in checks if c["passed"]) / len(checks)) if checks else 0.0
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))