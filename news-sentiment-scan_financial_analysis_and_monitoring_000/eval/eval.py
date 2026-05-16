import sys
import json
import subprocess
import re
from pathlib import Path

def find_report(workspace):
    """Find sentiment_report.json anywhere in workspace."""
    workspace = Path(workspace)
    candidates = list(workspace.rglob("sentiment_report.json"))
    return candidates[0] if candidates else None

def run_scan(stock_code, days, extra_args=None):
    """Run the sentiment scan script and capture output."""
    cmd = ["python3", "/skill/scripts/sentiment_scan.py", stock_code, str(days)]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def extract_score_from_output(output):
    """Extract the overall sentiment score from scan output."""
    # Match pattern: 情绪温度计：{score}（
    match = re.search(r'情绪温度计[：:]\s*([-+]?\d+\.?\d*)', output)
    if match:
        return float(match.group(1))
    return None

def score_to_expected_label(score):
    """Map score to expected Chinese label per SKILL.md."""
    if score >= 8:
        return "极度乐观"
    elif score >= 5:
        return "偏正面"
    elif score >= 2:
        return "轻微正面"
    elif score >= -2:
        return "中性"
    elif score >= -5:
        return "轻微负面"
    elif score >= -8:
        return "偏负面"
    else:
        return "极度悲观"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    
    # -------------------------------------------------------------------
    # CHECK 1: sentiment_report.json exists
    # -------------------------------------------------------------------
    report_path = find_report(workspace)
    check1 = {
        "name": "sentiment_report.json exists",
        "passed": report_path is not None,
        "detail": f"Found at {report_path}" if report_path else "File not found anywhere in workspace"
    }
    checks.append(check1)
    
    if not report_path:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return
    
    # -------------------------------------------------------------------
    # CHECK 2: JSON is valid and has required top-level keys
    # -------------------------------------------------------------------
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        
        required_keys = ["stocks"]
        has_keys = all(k in report for k in required_keys)
        check2 = {
            "name": "JSON structure has 'stocks' key",
            "passed": has_keys,
            "detail": f"Keys present: {list(report.keys())}"
        }
    except Exception as e:
        check2 = {
            "name": "JSON structure has 'stocks' key",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        }
        report = None
    checks.append(check2)
    
    if not report:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return
    
    # -------------------------------------------------------------------
    # CHECK 3: All 3 required stocks are present in report
    # -------------------------------------------------------------------
    stocks_data = report.get("stocks", {})
    
    # Determine which stock entries cover Tencent, Apple, Moutai
    # Accept various representations
    tencent_keys = {"0700.HK", "00700", "0700", "tencent", "腾讯", "TENCENT"}
    apple_keys = {"AAPL", "aapl", "apple", "苹果"}
    moutai_keys = {"600519", "moutai", "茅台", "贵州茅台"}
    
    def find_stock_entry(stocks_dict, key_set):
        for k in stocks_dict:
            if k.upper() in {x.upper() for x in key_set} or k in key_set:
                return k, stocks_dict[k]
        return None, None
    
    tencent_key, tencent_entry = find_stock_entry(stocks_data, tencent_keys)
    apple_key, apple_entry = find_stock_entry(stocks_data, apple_keys)
    moutai_key, moutai_entry = find_stock_entry(stocks_data, moutai_keys)
    
    all_three = all([tencent_entry is not None, apple_entry is not None, moutai_entry is not None])
    check3 = {
        "name": "All 3 portfolio stocks present (Tencent/AAPL/Moutai)",
        "passed": all_three,
        "detail": f"Tencent: {'found as '+tencent_key if tencent_key else 'MISSING'}, "
                  f"Apple: {'found as '+apple_key if apple_key else 'MISSING'}, "
                  f"Moutai: {'found as '+moutai_key if moutai_key else 'MISSING'}"
    }
    checks.append(check3)
    
    # -------------------------------------------------------------------
    # CHECK 4: Tencent was scanned with CORRECT HK format (not raw '700')
    # The error log hints that '700' fails. Must use '0700.HK' or '00700'.
    # We verify by running the scan ourselves and comparing scores.
    # -------------------------------------------------------------------
    try:
        # Run with correct format 0700.HK for 14 days (per portfolio config)
        correct_result = run_scan("0700.HK", 14)
        correct_score = extract_score_from_output(correct_result.stdout)
        
        # Run with wrong format '700' — should fail (exit code != 0)
        wrong_result = run_scan("700", 14)
        wrong_format_fails = wrong_result.returncode != 0
        
        if tencent_entry and correct_score is not None:
            reported_score = None
            if isinstance(tencent_entry, dict):
                reported_score = tencent_entry.get("sentiment_score") or tencent_entry.get("score") or tencent_entry.get("overall_score")
            
            # Score should match the correct scan output (within tolerance 0.5)
            score_matches = (
                reported_score is not None and 
                abs(float(reported_score) - correct_score) <= 0.5
            )
            check4 = {
                "name": "Tencent scanned with correct HK format (0700.HK or 00700), wrong '700' fails",
                "passed": score_matches and wrong_format_fails,
                "detail": (
                    f"Correct format '0700.HK' gives score {correct_score}. "
                    f"Reported score: {reported_score}. "
                    f"Wrong format '700' exit code: {wrong_result.returncode} (should be non-zero)."
                )
            }
        else:
            check4 = {
                "name": "Tencent scanned with correct HK format (0700.HK or 00700), wrong '700' fails",
                "passed": False,
                "detail": f"Could not verify: tencent_entry={tencent_entry}, correct_score={correct_score}"
            }
    except Exception as e:
        check4 = {
            "name": "Tencent scanned with correct HK format (0700.HK or 00700), wrong '700' fails",
            "passed": False,
            "detail": f"Error during verification: {e}"
        }
    checks.append(check4)
    
    # -------------------------------------------------------------------
    # CHECK 5: Sentiment scores are in valid range [-10, +10]
    # -------------------------------------------------------------------
    score_range_ok = True
    score_range_detail = []
    
    for key, entry in [("Tencent", tencent_entry), ("AAPL", apple_entry), ("Moutai", moutai_entry)]:
        if entry and isinstance(entry, dict):
            score = entry.get("sentiment_score") or entry.get("score") or entry.get("overall_score")
            if score is not None:
                try:
                    s = float(score)
                    if -10 <= s <= 10:
                        score_range_detail.append(f"{key}: {s} ✓")
                    else:
                        score_range_ok = False
                        score_range_detail.append(f"{key}: {s} ✗ (out of range)")
                except:
                    score_range_ok = False
                    score_range_detail.append(f"{key}: invalid value '{score}'")
            else:
                score_range_ok = False
                score_range_detail.append(f"{key}: score field missing")
        elif entry is None:
            score_range_detail.append(f"{key}: entry missing")
    
    check5 = {
        "name": "All sentiment scores in valid range [-10, +10]",
        "passed": score_range_ok and len(score_range_detail) == 3,
        "detail": "; ".join(score_range_detail)
    }
    checks.append(check5)
    
    # -------------------------------------------------------------------
    # CHECK 6: Emotion labels match the SKILL.md proprietary table
    # -------------------------------------------------------------------
    label_check_ok = True
    label_details = []
    
    for key, entry in [("Tencent", tencent_entry), ("AAPL", apple_entry), ("Moutai", moutai_entry)]:
        if entry and isinstance(entry, dict):
            score = entry.get("sentiment_score") or entry.get("score") or entry.get("overall_score")
            label = entry.get("sentiment_label") or entry.get("label") or entry.get("emotion_label")
            if score is not None and label is not None:
                expected_label = score_to_expected_label(float(score))
                # Check if label contains expected Chinese term
                if expected_label in str(label):
                    label_details.append(f"{key}: score={score}, label='{label}' matches '{expected_label}' ✓")
                else:
                    label_check_ok = False
                    label_details.append(f"{key}: score={score}, label='{label}' does NOT match expected '{expected_label}' ✗")
            else:
                label_check_ok = False
                label_details.append(f"{key}: missing score or label (score={score}, label={label})")
    
    check6 = {
        "name": "Emotion labels correctly mapped per SKILL.md scoring table",
        "passed": label_check_ok and len(label_details) >= 2,
        "detail": "; ".join(label_details) if label_details else "No label data found"
    }
    checks.append(check6)
    
    # -------------------------------------------------------------------
    # CHECK 7: Event list present for each stock
    # -------------------------------------------------------------------
    events_present = True
    events_detail = []
    
    for key, entry in [("Tencent", tencent_entry), ("AAPL", apple_entry), ("Moutai", moutai_entry)]:
        if entry and isinstance(entry, dict):
            events = entry.get("events") or entry.get("major_events") or entry.get("event_list")
            if events and isinstance(events, list) and len(events) >= 2:
                events_detail.append(f"{key}: {len(events)} events ✓")
            else:
                events_present = False
                events_detail.append(f"{key}: events missing or < 2 items ✗")
    
    check7 = {
        "name": "Event lists present for all stocks (>=2 events each)",
        "passed": events_present,
        "detail": "; ".join(events_detail) if events_detail else "No event data found"
    }
    checks.append(check7)
    
    # -------------------------------------------------------------------
    # CHECK 8: Monitoring days respected (Tencent=14, AAPL=7, Moutai=7)
    # -------------------------------------------------------------------
    days_check_ok = True
    days_detail = []
    
    for key, entry, expected_days in [
        ("Tencent", tencent_entry, 14), 
        ("AAPL", apple_entry, 7), 
        ("Moutai", moutai_entry, 7)
    ]:
        if entry and isinstance(entry, dict):
            days_val = entry.get("monitoring_days") or entry.get("days") or entry.get("period_days")
            if days_val is not None:
                try:
                    if int(days_val) == expected_days:
                        days_detail.append(f"{key}: {days_val} days ✓")
                    else:
                        days_check_ok = False
                        days_detail.append(f"{key}: {days_val} days, expected {expected_days} ✗")
                except:
                    days_check_ok = False
                    days_detail.append(f"{key}: invalid days value '{days_val}'")
            else:
                # Tolerate missing days field as long as other checks pass
                days_detail.append(f"{key}: days field not recorded (tolerated)")
    
    check8 = {
        "name": "Per-stock monitoring days match portfolio config (Tencent=14, AAPL=7, Moutai=7)",
        "passed": days_check_ok,
        "detail": "; ".join(days_detail) if days_detail else "No days data found"
    }
    checks.append(check8)
    
    # -------------------------------------------------------------------
    # Compute final score
    # -------------------------------------------------------------------
    critical_checks = [checks[0], checks[1], checks[2], checks[3]]  # existence, structure, 3-stocks, correct format
    bonus_checks = [checks[4], checks[5], checks[6], checks[7]]      # range, labels, events, days
    
    critical_passed = sum(1 for c in critical_checks if c["passed"])
    bonus_passed = sum(1 for c in bonus_checks if c["passed"])
    
    all_passed = all(c["passed"] for c in checks)
    
    score = (critical_passed / len(critical_checks)) * 0.6 + (bonus_passed / len(bonus_checks)) * 0.4
    
    result = {
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()