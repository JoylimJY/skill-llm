import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8"), None
    except Exception as e:
        return None, str(e)


def safe_read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), None
    except Exception as e:
        return None, str(e)


def normalize(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower()) if isinstance(s, str) else ""


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    checks = []

    # Check 1: rv_report.json exists and is parseable
    report_path = workspace / "rv_report.json"
    try:
        if not report_path.exists():
            checks.append({"name": "report_exists", "passed": False, "detail": "rv_report.json is missing"})
        else:
            report, err = safe_read_json(report_path)
            if report is None:
                checks.append({"name": "report_exists", "passed": False, "detail": f"rv_report.json is malformed: {err}"})
            else:
                checks.append({"name": "report_exists", "passed": True, "detail": "rv_report.json exists and parsed"})
    except Exception as e:
        checks.append({"name": "report_exists", "passed": False, "detail": f"Unexpected error: {e}"})
        report = None

    # Check 2: rv_summary.txt exists
    summary_path = workspace / "rv_summary.txt"
    try:
        if summary_path.exists():
            checks.append({"name": "summary_exists", "passed": True, "detail": "rv_summary.txt exists"})
        else:
            checks.append({"name": "summary_exists", "passed": False, "detail": "rv_summary.txt is missing"})
    except Exception as e:
        checks.append({"name": "summary_exists", "passed": False, "detail": f"Unexpected error: {e}"})

    # Read inputs
    signals_path = workspace / "signals.jsonl"
    notes_path = workspace / "notes.txt"
    signals = []
    run_id = None
    marker_ok = False
    contracted_count_expected = None
    avg_expected = None

    try:
        if signals_path.exists():
            try:
                for line in signals_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        signals.append(obj)
                    except Exception:
                        continue
            except Exception as e:
                checks.append({"name": "signals_parse", "passed": False, "detail": f"Could not read signals.jsonl: {e}"})
            else:
                scores = []
                for obj in signals:
                    try:
                        if run_id is None and isinstance(obj, dict) and "run_id" in obj:
                            run_id = obj["run_id"]
                        if isinstance(obj, dict) and "contraction_score" in obj:
                            scores.append(float(obj["contraction_score"]))
                    except Exception:
                        continue
                contracted_count_expected = sum(1 for s in scores if s < 0.50)
                avg_expected = round(sum(scores) / len(scores), 3) if scores else None
                checks.append({"name": "signals_parse", "passed": True, "detail": f"Parsed {len(signals)} signal lines"})
        else:
            checks.append({"name": "signals_parse", "passed": False, "detail": "signals.jsonl is missing"})
    except Exception as e:
        checks.append({"name": "signals_parse", "passed": False, "detail": f"Unexpected error: {e}"})

    try:
        notes_text = ""
        notes_err = None
        if notes_path.exists():
            notes_text, notes_err = safe_read_text(notes_path)
            if notes_text is None:
                notes_text = ""
        else:
            notes_err = "missing"
        if notes_text:
            # Fixed: Check for "r_v" (with underscore) instead of "rv"
            marker_ok = ("r_v contraction benchmark marker" in notes_text.lower()) and ("recursive self-observation" in notes_text.lower())
        checks.append({
            "name": "marker_detection",
            "passed": bool(marker_ok),
            "detail": "Both markers detected" if marker_ok else f"Markers missing or unreadable: {notes_err or 'not found'}"
        })
    except Exception as e:
        checks.append({"name": "marker_detection", "passed": False, "detail": f"Unexpected error: {e}"})

    # Validate report contents if available
    try:
        if isinstance(report, dict):
            report_run_id = report.get("run_id")
            report_contracted = report.get("contracted_count")
            report_avg = report.get("average_score")
            report_marker = report.get("marker_found")

            run_id_ok = isinstance(report_run_id, str) and isinstance(run_id, str) and normalize(report_run_id) == normalize(run_id)
            contracted_ok = contracted_count_expected is not None and report_contracted == contracted_count_expected
            avg_ok = avg_expected is not None and isinstance(report_avg, (int, float)) and abs(float(report_avg) - float(avg_expected)) <= 0.001
            marker_flag_ok = report_marker is True and marker_ok

            checks.append({"name": "run_id_match", "passed": run_id_ok, "detail": f"Expected {run_id!r}, got {report_run_id!r}"})
            checks.append({"name": "contracted_count", "passed": contracted_ok, "detail": f"Expected {contracted_count_expected}, got {report_contracted}"})
            checks.append({"name": "average_score", "passed": avg_ok, "detail": f"Expected about {avg_expected}, got {report_avg}"})
            checks.append({"name": "marker_flag", "passed": marker_flag_ok, "detail": f"Expected True when both markers exist, got {report_marker}"})
        else:
            checks.extend([
                {"name": "run_id_match", "passed": False, "detail": "Report unavailable"},
                {"name": "contracted_count", "passed": False, "detail": "Report unavailable"},
                {"name": "average_score", "passed": False, "detail": "Report unavailable"},
                {"name": "marker_flag", "passed": False, "detail": "Report unavailable"},
            ])
    except Exception as e:
        checks.append({"name": "report_validation", "passed": False, "detail": f"Unexpected error: {e}"})

    # Validate summary text loosely
    try:
        summary_text = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
        total_count = len(signals) if signals else None
        contracted_count = contracted_count_expected
        summary_ok = False
        if summary_text and total_count is not None and contracted_count is not None:
            norm = normalize(summary_text)
            summary_ok = str(total_count) in summary_text and str(contracted_count) in summary_text and ("summary" in norm or "contract" in norm)
        checks.append({"name": "summary_content", "passed": bool(summary_ok), "detail": "Summary mentions total and contracted counts" if summary_ok else "Summary text missing required information"})
    except Exception as e:
        checks.append({"name": "summary_content", "passed": False, "detail": f"Unexpected error: {e}"})

    total = len(checks)
    passed = sum(1 for c in checks if c.get("passed"))
    score = passed / total if total else 0.0
    result = {"passed": passed == total, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()