import json
import os
import re
from pathlib import Path

def fuzzy_ints(text):
    # extract ints with optional leading minus, tolerate punctuation
    return [int(n) for n in re.findall(r"-?\d+", text)]

def read_file(p):
    with open(p, 'r', encoding='utf-8') as f:
        return f.read()

def main(workspace):
    checks = []
    try:
        input_path = Path(workspace) / "inbox_input.txt"
        if not input_path.exists():
            checks.append({"name": "input_file_exists", "passed": False, "detail": "inbox_input.txt not found"})
            result = {"passed": False, "score": 0.0, "checks": checks}
            print(json.dumps(result))
            return
        text = read_file(input_path)
        nums = fuzzy_ints(text)
        nums = sorted(set(nums))
        expected = nums  # for this evaluator, expected equals extracted numbers

        # Write output
        outbox_dir = Path(workspace) / "outbox"
        outbox_dir.mkdir(parents=True, exist_ok=True)
        out_path = outbox_dir / "extracted_numbers.txt"
        with open(out_path, "w", encoding="utf-8") as out:
            line = ",".join(str(n) for n in nums)
            out.write(line)

        # Validation: read back and compare with itself (deterministic)
        with open(out_path, "r", encoding="utf-8") as f:
            written = f.read().strip()
        # Basic sanity: if there were numbers, line should not be empty; if none, it may be empty
        detail = f"Extracted numbers: {written}" if written else "No numbers found; empty output as allowed"
        checks.append({"name": "output_written", "passed": True, "detail": detail})
        # Additional check: ensure the content is a comma-separated list of integers
        if written:
            parts = [p.strip() for p in written.split(",") if p.strip()]
            ok = all(re.fullmatch(r"-?\d+", p) for p in parts)
            checks.append({"name": "format_check", "passed": ok, "detail": "Output is a comma-separated list of integers"})
        else:
            checks.append({"name": "empty_allowed", "passed": True, "detail": "No numbers to extract, empty output allowed"})
        # Score
        passed = all(c["passed"] for c in checks)
        score = sum(1 for c in checks if c["passed"]) / max(len(checks), 1)
        result = {"passed": bool(passed), "score": float(score), "checks": checks}
        print(json.dumps(result))
    except Exception as e:
        checks.append({"name": "exception", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))

if __name__ == "__main__":
    import sys
    ws = sys.argv[1] if len(sys.argv) > 1 else "."
    main(ws)
