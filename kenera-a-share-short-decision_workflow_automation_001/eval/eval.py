import sys
import json
import os
import pathlib

workspace = sys.argv[1]
ws = pathlib.Path(workspace)

checks = []
total_score = 0.0

def check(name, condition, detail, weight=1.0):
    checks.append({"name": name, "passed": condition, "detail": detail})
    return weight if condition else 0.0

# ── CHECK 1: decision_log.jsonl has a new entry for 2026-02-12 ──────────────
log_file = ws / "data" / "decision_log.jsonl"
prediction_entry = None
try:
    entries = []
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            entries.append(obj)

    # Find entry for 2026-02-12
    for obj in entries:
        if obj.get("prediction_date") == "2026-02-12" or obj.get("analysis_date") == "2026-02-12":
            prediction_entry = obj
            break

    c1 = prediction_entry is not None
    detail1 = f"Found {len(entries)} total entries in decision_log.jsonl. " + (
        "Entry for 2026-02-12 EXISTS." if c1 else "NO entry found for 2026-02-12."
    )
    total_score += check(
        "prediction_logged_for_20260212",
        c1,
        detail1,
        weight=1.0,
    )
except Exception as e:
    total_score += check(
        "prediction_logged_for_20260212",
        False,
        f"EXCEPTION reading decision_log.jsonl: {e}",
        weight=1.0,
    )

# ── CHECK 2: prediction entry has correct structure (candidates, signal) ────
try:
    if prediction_entry is not None:
        has_signal = "signal" in prediction_entry
        has_candidates = "candidates" in prediction_entry
        has_score = "score" in prediction_entry
        c2 = has_signal and has_candidates and has_score
        detail2 = (
            f"signal={prediction_entry.get('signal')}, "
            f"candidates_count={len(prediction_entry.get('candidates', []))}, "
            f"score={prediction_entry.get('score')}. "
            f"has_signal={has_signal}, has_candidates={has_candidates}, has_score={has_score}"
        )
    else:
        c2 = False
        detail2 = "No prediction entry found, cannot check structure."
    total_score += check(
        "prediction_entry_has_required_fields",
        c2,
        detail2,
        weight=0.5,
    )
except Exception as e:
    total_score += check(
        "prediction_entry_has_required_fields",
        False,
        f"EXCEPTION: {e}",
        weight=0.5,
    )

# ── CHECK 3: daily report for 2026-02-12 was generated ──────────────────────
report_path = ws / "data" / "reports" / "daily_report_2026-02-12.json"
report_data = None
try:
    if report_path.exists():
        with open(report_path, encoding="utf-8") as f:
            report_data = json.load(f)
        c3 = True
        detail3 = f"Report file exists at {report_path}. report_date={report_data.get('report_date')}"
    else:
        # Also search recursively in case agent saved elsewhere
        found_reports = list(ws.rglob("daily_report_2026-02-12.json"))
        if found_reports:
            with open(found_reports[0], encoding="utf-8") as f:
                report_data = json.load(f)
            c3 = True
            detail3 = f"Report file found at alternate path: {found_reports[0]}"
        else:
            c3 = False
            detail3 = "daily_report_2026-02-12.json NOT found anywhere in workspace."
    total_score += check("daily_report_generated", c3, detail3, weight=1.0)
except Exception as e:
    total_score += check("daily_report_generated", False, f"EXCEPTION: {e}", weight=1.0)

# ── CHECK 4: report has correct date and required fields ────────────────────
try:
    if report_data is not None:
        correct_date = report_data.get("report_date") == "2026-02-12"
        has_signal_summary = "signal_summary" in report_data
        has_recommendation = "recommendation" in report_data
        has_risk_note = "risk_note" in report_data
        c4 = correct_date and has_signal_summary and has_recommendation
        detail4 = (
            f"correct_date={correct_date}, "
            f"has_signal_summary={has_signal_summary}, "
            f"has_recommendation={has_recommendation}, "
            f"has_risk_note={has_risk_note}"
        )
    else:
        c4 = False
        detail4 = "No report data to validate."
    total_score += check("report_content_valid", c4, detail4, weight=0.5)
except Exception as e:
    total_score += check("report_content_valid", False, f"EXCEPTION: {e}", weight=0.5)

# ── CHECK 5: comparison between 2026-02-12 prediction and 2026-02-13 actual ─
# Evidence: either a comparison JSON artifact, or we look for comparison output
# The compare command prints to stdout — we can infer it ran if prediction was 
# logged AND market data was present. We look for any JSON artifact or infer.
comparison_artifact = None
try:
    # Search for any comparison output file
    comparison_candidates = list(ws.rglob("*comparison*")) + list(ws.rglob("*compare*"))
    comparison_candidates = [p for p in comparison_candidates if p.is_file() and p.suffix in ('.json', '.txt', '.log', '.jsonl')]
    
    found_comparison = False
    comparison_detail = ""
    
    for cp in comparison_candidates:
        try:
            with open(cp, encoding="utf-8") as f:
                content = f.read()
            if "2026-02-12" in content and "2026-02-13" in content:
                found_comparison = True
                comparison_detail = f"Found comparison artifact at {cp} referencing both dates."
                comparison_artifact = content
                break
            elif "2026-02-12" in content and "per_stock_returns" in content:
                found_comparison = True
                comparison_detail = f"Found comparison artifact at {cp} with per_stock_returns."
                comparison_artifact = content
                break
        except Exception:
            continue
    
    # Also check if there's a combined report that includes comparison data
    if not found_comparison and report_data is not None:
        if "comparison" in report_data or "per_stock_returns" in report_data:
            found_comparison = True
            comparison_detail = "Comparison data found embedded in daily report."
    
    # Alternative: check for any file in data/ that references actual_date 2026-02-13
    if not found_comparison:
        for p in ws.rglob("*.json"):
            try:
                with open(p, encoding="utf-8") as f:
                    text = f.read()
                if "2026-02-13" in text and "per_stock" in text:
                    found_comparison = True
                    comparison_detail = f"Comparison result found in {p}"
                    break
                elif "2026-02-13" in text and "actual_date" in text:
                    found_comparison = True
                    comparison_detail = f"Comparison result (actual_date field) found in {p}"
                    break
            except Exception:
                continue

    # Also check for JSONL entries that might capture comparison
    if not found_comparison:
        for p in ws.rglob("*.jsonl"):
            try:
                with open(p, encoding="utf-8") as f:
                    text = f.read()
                if "actual_date" in text and "2026-02-13" in text:
                    found_comparison = True
                    comparison_detail = f"Comparison log entry found in {p}"
                    break
            except Exception:
                continue

    if not found_comparison:
        comparison_detail = (
            "No comparison artifact found referencing prediction_date=2026-02-12 "
            "and actual_date=2026-02-13. Agent may have run comparison but not saved output, "
            "OR agent skipped this step entirely."
        )

    total_score += check(
        "comparison_run_for_20260212_vs_20260213",
        found_comparison,
        comparison_detail,
        weight=1.0,
    )
except Exception as e:
    total_score += check(
        "comparison_run_for_20260212_vs_20260213",
        False,
        f"EXCEPTION: {e}",
        weight=1.0,
    )

# ── CHECK 6: no_recommendation_message present when NO_TRADE ────────────────
# If the 2026-02-12 prediction is NO_TRADE, the entry MUST contain no_recommendation_message
try:
    if prediction_entry is not None and prediction_entry.get("signal") == "NO_TRADE":
        has_msg = "no_recommendation_message" in prediction_entry
        msg_correct = "当前暂无可执行短线买入标的" in prediction_entry.get("no_recommendation_message", "")
        c6 = has_msg and msg_correct
        detail6 = (
            f"NO_TRADE signal detected. has_no_recommendation_message={has_msg}, "
            f"msg_correct={msg_correct}. "
            f"msg='{prediction_entry.get('no_recommendation_message', '')}'"
        )
        total_score += check("no_trade_message_compliance", c6, detail6, weight=0.5)
    else:
        # BUY signal - check that candidates are populated
        if prediction_entry is not None and prediction_entry.get("signal") == "BUY":
            candidates = prediction_entry.get("candidates", [])
            c6 = len(candidates) > 0
            detail6 = f"BUY signal: {len(candidates)} candidates in prediction. Expected > 0."
        else:
            c6 = True  # not applicable
            detail6 = "Check not applicable (no prediction entry or ambiguous signal)."
        total_score += check("no_trade_message_compliance", c6, detail6, weight=0.5)
except Exception as e:
    total_score += check("no_trade_message_compliance", False, f"EXCEPTION: {e}", weight=0.5)

# ── Final scoring ────────────────────────────────────────────────────────────
max_score = 4.5  # sum of all weights
normalized = round(total_score / max_score, 3)

passed = (
    checks[0]["passed"]  # prediction logged
    and checks[2]["passed"]  # daily report generated
    and checks[3]["passed"]  # report content valid
)

print(json.dumps({
    "passed": passed,
    "score": normalized,
    "checks": checks,
}, ensure_ascii=False, indent=2))