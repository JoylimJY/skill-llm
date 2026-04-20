import json
import csv
from pathlib import Path
import sys

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    inp = workspace / "chat_logs.jsonl"
    add_check("input_exists", inp.exists(), "chat_logs.jsonl exists" if inp.exists() else "chat_logs.jsonl is missing")
except Exception as e:
    add_check("input_exists", False, f"error checking input: {e}")

try:
    marker = workspace / "marker.txt"
    content = marker.read_text(encoding="utf-8") if marker.exists() else ""
    ok = "groq_task_marker" in content.lower()
    add_check("marker_present", ok, "marker found" if ok else "marker missing or incorrect")
except Exception as e:
    add_check("marker_present", False, f"error reading marker: {e}")

try:
    out = workspace / "user_summary.csv"
    if not out.exists():
        add_check("output_exists", False, "user_summary.csv is missing")
    else:
        rows = []
        try:
            with out.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            add_check("output_parsable", False, f"could not parse CSV: {e}")
        else:
            header_ok = set((reader.fieldnames or [])) >= {"id", "role", "message_length", "has_question_mark"}
            add_check("header_ok", header_ok, "required columns present" if header_ok else f"found headers: {reader.fieldnames}")
            user_ids = []
            for r in rows:
                try:
                    if str(r.get("role", "")).strip().lower() == "user":
                        user_ids.append(str(r.get("id", "")).strip())
                except Exception:
                    pass
            expected_ids = ["a1", "c3", "e5"]
            ids_ok = user_ids[:3] == expected_ids
            add_check("user_rows_in_order", ids_ok, f"user ids: {user_ids}" )
            lengths_ok = True
            questions_ok = True
            for r in rows:
                try:
                    if str(r.get("role", "")).strip().lower() != "user":
                        continue
                    mid = str(r.get("id", "")).strip()
                    msg = {"a1": "What is the Groq API latency like?", "c3": "Please summarize this dataset.", "e5": "Is there a question mark here"}.get(mid, "")
                    got_len = int(str(r.get("message_length", "")).strip())
                    if got_len != len(msg):
                        lengths_ok = False
                    got_q = str(r.get("has_question_mark", "")).strip().lower()
                    expected_q = "true" if "?" in msg else "false"
                    if got_q not in {expected_q, "1" if expected_q == "true" else "0"}:
                        questions_ok = False
                except Exception:
                    lengths_ok = False
                    questions_ok = False
            add_check("message_lengths", lengths_ok, "message lengths match expected values" if lengths_ok else "one or more lengths mismatch")
            add_check("question_mark_flags", questions_ok, "question mark flags are correct" if questions_ok else "one or more flags mismatch")
except Exception as e:
    add_check("output_checks", False, f"error checking output: {e}")

passed = all(c["passed"] for c in checks)
score = (sum(1 for c in checks if c["passed"]) / len(checks)) if checks else 0.0
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
