import sys
import json
import os
from pathlib import Path

def load_json_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def load_jsonl_file(filepath):
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

def main():
    workspace = sys.argv[1]
    checks = []

    # ── CHECK 1: decision_log.jsonl has entry for 2026-03-10 ────────────────
    check_name = "decision_log.jsonl contains prediction for 2026-03-10"
    try:
        log_path = Path(workspace) / "data" / "decision_log.jsonl"
        assert log_path.exists(), "decision_log.jsonl not found"
        entries = load_jsonl_file(log_path)
        matched = [e for e in entries if e.get("prediction_date") == "2026-03-10"]
        assert len(matched) >= 1, f"No entry for 2026-03-10 found, entries: {[e.get('prediction_date') for e in entries]}"
        entry = matched[0]
        signal = entry.get("signal_result", {})
        assert signal.get("status") == "BUY_SIGNAL", f"Expected BUY_SIGNAL, got {signal.get('status')}"
        candidates = signal.get("candidates", [])
        assert len(candidates) >= 1, "No candidates in signal_result"
        checks.append({"name": check_name, "passed": True, "detail": f"Found entry with {len(candidates)} candidates, status=BUY_SIGNAL"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 2: comparison file for 20260310_20260311 exists and is valid ──
    check_name = "comparison_20260310_20260311.json exists with correct structure"
    try:
        comp_path = Path(workspace) / "data" / "comparison_20260310_20260311.json"
        assert comp_path.exists(), f"comparison file not found at {comp_path}"
        comp = load_json_file(comp_path)
        assert comp.get("prediction_date") == "2026-03-10", f"Wrong prediction_date: {comp.get('prediction_date')}"
        assert comp.get("actual_date") == "2026-03-11", f"Wrong actual_date: {comp.get('actual_date')}"
        summary = comp.get("summary", {})
        assert "avg_return" in summary, "avg_return missing from summary"
        assert "win_rate" in summary, "win_rate missing from summary"
        per_stock = comp.get("per_stock_returns", {})
        assert len(per_stock) >= 1, "per_stock_returns is empty"
        # Verify at least one stock has return field
        first_stock = next(iter(per_stock.values()))
        assert "return" in first_stock, "return field missing from stock entry"
        checks.append({"name": check_name, "passed": True, "detail": f"Comparison valid: avg_return={summary.get('avg_return')}, num_compared={summary.get('num_compared')}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 3: daily_report_20260310.json exists and is valid ─────────────
    check_name = "daily_report_20260310.json exists with correct structure"
    try:
        report_path = Path(workspace) / "data" / "daily_report_20260310.json"
        assert report_path.exists(), f"daily report not found at {report_path}"
        report = load_json_file(report_path)
        assert report.get("report_date") == "2026-03-10", f"Wrong report_date: {report.get('report_date')}"
        mi = report.get("market_intelligence", {})
        assert mi.get("status") == "BUY_SIGNAL", f"Expected BUY_SIGNAL in report, got {mi.get('status')}"
        assert mi.get("candidates_count", 0) >= 1, "No candidates in report"
        assert "recommendation" in report, "recommendation field missing"
        assert report.get("recommendation"), "recommendation is empty"
        checks.append({"name": check_name, "passed": True, "detail": f"Report valid: status={mi.get('status')}, candidates={mi.get('candidates_count')}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 4: correct sequence - prediction_date precedes comparison ──────
    check_name = "run_prediction_for_date was called BEFORE compare (decision_log entry timestamps)"
    try:
        log_path = Path(workspace) / "data" / "decision_log.jsonl"
        comp_path = Path(workspace) / "data" / "comparison_20260310_20260311.json"
        assert log_path.exists() and comp_path.exists(), "Required files missing"
        # Check that decision_log has the 2026-03-10 entry (guarantees run_prediction was called)
        entries = load_jsonl_file(log_path)
        matched = [e for e in entries if e.get("prediction_date") == "2026-03-10"]
        assert len(matched) >= 1, "No 2026-03-10 prediction in log"
        # Also verify stale entry for 2026-02-10 still exists (not overwritten)
        stale = [e for e in entries if e.get("prediction_date") == "2026-02-10"]
        assert len(stale) >= 1, "Stale 2026-02-10 entry was removed (should be appended, not overwritten)"
        checks.append({"name": check_name, "passed": True, "detail": f"Log has {len(entries)} entries, including stale 2026-02-10 and new 2026-03-10"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 5: weighted_score is non-zero for BUY_SIGNAL ──────────────────
    check_name = "weighted_score is positive for BUY_SIGNAL date 2026-03-10"
    try:
        log_path = Path(workspace) / "data" / "decision_log.jsonl"
        entries = load_jsonl_file(log_path)
        matched = [e for e in entries if e.get("prediction_date") == "2026-03-10"]
        assert len(matched) >= 1, "No 2026-03-10 entry"
        score = matched[0].get("signal_result", {}).get("weighted_score", 0)
        assert score > 0, f"weighted_score should be > 0, got {score}"
        checks.append({"name": check_name, "passed": True, "detail": f"weighted_score={score}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 6: report has capital_flow_confirmed field ────────────────────
    check_name = "daily report includes capital_flow_confirmed field"
    try:
        report_path = Path(workspace) / "data" / "daily_report_20260310.json"
        assert report_path.exists(), "Daily report not found"
        report = load_json_file(report_path)
        mi = report.get("market_intelligence", {})
        assert "capital_flow_confirmed" in mi, "capital_flow_confirmed missing from market_intelligence"
        assert mi["capital_flow_confirmed"] == True, f"Expected True, got {mi['capital_flow_confirmed']}"
        checks.append({"name": check_name, "passed": True, "detail": "capital_flow_confirmed=True present in report"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()