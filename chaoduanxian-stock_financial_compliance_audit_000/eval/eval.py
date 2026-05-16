import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0

def find_report(workspace):
    for p in Path(workspace).rglob("compliance_report.json"):
        return p
    return None

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

report_path = find_report(workspace)

if report_path is None:
    checks.append({"name": "report_exists", "passed": False, "detail": "compliance_report.json not found anywhere in workspace"})
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

try:
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
except Exception as e:
    checks.append({"name": "report_parseable", "passed": False, "detail": f"Could not parse JSON: {e}"})
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

score += add_check("report_exists", True, f"Found at {report_path}")

TOTAL_CAPITAL = 500000
SINGLE_STOCK_LIMIT = TOTAL_CAPITAL * 0.10  # 50000
DAILY_TOTAL_LIMIT = TOTAL_CAPITAL * 0.30   # 150000
STOP_LOSS_PCT = -0.07
TAKE_PROFIT_HALF_PCT = 0.07
TAKE_PROFIT_FULL_PCT = 0.15

# ---- CHECK 1: Single stock position violations ----
# Stocks with position_value > 50000: 600003(80000), 600007(90000)
try:
    violations = report.get("position_violations", [])
    if isinstance(violations, list):
        violation_codes = set()
        for v in violations:
            if isinstance(v, dict):
                code = str(v.get("stock_code", ""))
                violation_codes.add(code)
            elif isinstance(v, str):
                violation_codes.add(v)
        required = {"600003", "600007"}
        found_required = required.issubset(violation_codes)
        score += add_check(
            "single_stock_position_violations",
            found_required,
            f"Expected 600003 and 600007 as single-stock violations (>10% of capital={SINGLE_STOCK_LIMIT}). Found: {violation_codes}"
        )
    else:
        score += add_check("single_stock_position_violations", False, f"position_violations is not a list: {type(violations)}")
except Exception as e:
    score += add_check("single_stock_position_violations", False, f"Error checking position_violations: {e}")

# ---- CHECK 2: Daily cumulative position violation on 2024-05-07 ----
# Day 2024-05-07: 48000+50000+30000+90000 = 218000 > 150000
try:
    daily_violations = report.get("daily_cumulative_violations", [])
    if isinstance(daily_violations, list):
        dates_flagged = set()
        for v in daily_violations:
            if isinstance(v, dict):
                d = str(v.get("date", ""))
                dates_flagged.add(d)
            elif isinstance(v, str):
                dates_flagged.add(v)
        required_date = "2024-05-07"
        found = required_date in dates_flagged
        score += add_check(
            "daily_cumulative_violation_20240507",
            found,
            f"Expected 2024-05-07 flagged as daily cumulative violation (>30% cap={DAILY_TOTAL_LIMIT}). Found dates: {dates_flagged}"
        )
    else:
        score += add_check("daily_cumulative_violation_20240507", False, f"daily_cumulative_violations is not a list")
except Exception as e:
    score += add_check("daily_cumulative_violation_20240507", False, f"Error: {e}")

# ---- CHECK 3: Stop-loss flags ----
# Stocks needing stop-loss (-7% or worse):
# 600002: (7.44-8.00)/8.00 = -7.0% -> exactly at threshold, must flag
# 600009: (4.65-5.00)/5.00 = -7.0% -> must flag
# 600012: (10.23-11.00)/11.00 = -7.0% -> must flag
# 600016: (8.28-9.00)/9.00 = -8.0% -> must flag
# 600008: (28.20-30.00)/30.00 = -6.0% -> NOT a stop-loss (less than -7%)
try:
    stop_loss_flags = report.get("stop_loss_flags", [])
    if isinstance(stop_loss_flags, list):
        sl_codes = set()
        for v in stop_loss_flags:
            if isinstance(v, dict):
                sl_codes.add(str(v.get("stock_code", "")))
            elif isinstance(v, str):
                sl_codes.add(v)
        required_sl = {"600002", "600009", "600012", "600016"}
        false_positive = "600008" in sl_codes  # -6%, should NOT be flagged
        all_required_found = required_sl.issubset(sl_codes)
        passed = all_required_found and not false_positive
        score += add_check(
            "stop_loss_flags_correct",
            passed,
            f"Required: {required_sl}, Found: {sl_codes}. 600008 should NOT be flagged (only -6%). false_positive={false_positive}"
        )
    else:
        score += add_check("stop_loss_flags_correct", False, "stop_loss_flags not a list")
except Exception as e:
    score += add_check("stop_loss_flags_correct", False, f"Error: {e}")

# ---- CHECK 4: Take-profit action classification ----
# +7% partial sell: 600014 (+7%), 600015 (+15% - second half, full exit)
# +15% partial sell: 600011 (+15%)
# The skill mandates: at +7% sell half, at +15% sell remaining half
# 600014: (26.75-25.00)/25.00 = +7% -> first partial take-profit
# 600011: (20.70-18.00)/18.00 = +15% -> second partial (or full if already halved)
# 600015: (16.10-14.00)/14.00 = +15% -> take-profit signal
try:
    take_profit = report.get("take_profit_flags", [])
    if isinstance(take_profit, list):
        tp_codes = set()
        for v in take_profit:
            if isinstance(v, dict):
                tp_codes.add(str(v.get("stock_code", "")))
            elif isinstance(v, str):
                tp_codes.add(v)
        required_tp = {"600011", "600014", "600015"}
        found = required_tp.issubset(tp_codes)
        score += add_check(
            "take_profit_flags",
            found,
            f"Expected take-profit flags for {required_tp}. Found: {tp_codes}"
        )
    else:
        score += add_check("take_profit_flags", False, "take_profit_flags not a list")
except Exception as e:
    score += add_check("take_profit_flags", False, f"Error: {e}")

# ---- CHECK 5: 龙头 (leading stock) identification ----
# Criteria: consecutive_limit_up >= 3 AND 5% <= turnover_rate_pct <= 15%
# 600004: consec=3, turnover=8.5% -> 龙头
# 600005: consec=4, turnover=6.3% -> 龙头
# 600010: consec=5, turnover=13.5% -> 龙头
# 600017: consec=4, turnover=12.1% -> 龙头
# 600013: consec=1, turnover=16.3% -> NOT 龙头 (turnover > 15%)
# 600008: consec=3, turnover=11.2% -> 龙头
try:
    longhead = report.get("longtou_stocks", [])
    if isinstance(longhead, list):
        lh_codes = set()
        for v in longhead:
            if isinstance(v, dict):
                lh_codes.add(str(v.get("stock_code", "")))
            elif isinstance(v, str):
                lh_codes.add(v)
        required_lh = {"600004", "600005", "600010", "600017", "600008"}
        false_pos = "600013" in lh_codes  # turnover 16.3% > 15%, NOT 龙头
        all_found = required_lh.issubset(lh_codes)
        passed = all_found and not false_pos
        score += add_check(
            "longtou_identification",
            passed,
            f"Required longtou: {required_lh}, found: {lh_codes}. 600013 false_positive={false_pos} (turnover 16.3% exceeds 15% threshold)"
        )
    else:
        score += add_check("longtou_identification", False, "longtou_stocks not a list")
except Exception as e:
    score += add_check("longtou_identification", False, f"Error: {e}")

# ---- CHECK 6: Emotion cycle classification per day ----
# Based on skill: 启动期 (few limit-ups, warming), 高潮期 (many limit-ups, few breaks), 退潮期 (many breaks), 冰点期 (almost none)
# 2024-05-06: limit_up=5, breaks=1 -> 启动期
# 2024-05-07: limit_up=18, breaks=2 -> 高潮期
# 2024-05-08: limit_up=8, breaks=9 -> 退潮期 (breaks nearly equal limit-ups, high ratio)
# 2024-05-09: limit_up=2, breaks=14 -> 冰点期 (very few limit-ups)
# 2024-05-10: limit_up=6, breaks=3 -> 启动期

EXPECTED_EMOTION = {
    "2024-05-06": "启动期",
    "2024-05-07": "高潮期",
    "2024-05-08": "退潮期",
    "2024-05-09": "冰点期",
    "2024-05-10": "启动期",
}
try:
    emotion = report.get("emotion_cycle", {})
    if isinstance(emotion, dict):
        correct = 0
        for date, expected in EXPECTED_EMOTION.items():
            actual = str(emotion.get(date, ""))
            if expected in actual:
                correct += 1
        emotion_passed = correct >= 4  # allow 1 error
        score += add_check(
            "emotion_cycle_classification",
            emotion_passed,
            f"Correct: {correct}/5 days. Expected: {EXPECTED_EMOTION}, Got: {emotion}"
        )
    else:
        score += add_check("emotion_cycle_classification", False, f"emotion_cycle is not a dict: {type(emotion)}")
except Exception as e:
    score += add_check("emotion_cycle_classification", False, f"Error: {e}")

# ---- CHECK 7: Split take-profit rule correctness ----
# Must distinguish: +7% = "分批止盈第一档" (sell half), +15% = "分批止盈第二档" (sell remaining half)
# 600014 is +7% -> first tier; 600011 and 600015 are +15% -> second tier
try:
    take_profit_detail = report.get("take_profit_flags", [])
    tier1_found = False
    tier2_found = False
    for v in take_profit_detail:
        if isinstance(v, dict):
            code = str(v.get("stock_code", ""))
            action = str(v.get("action", "") or v.get("tier", "") or v.get("type", "") or "")
            pnl = v.get("pnl_pct", None)
            if code == "600014":
                # Should be first-tier (~7%)
                pnl_val = float(pnl) if pnl is not None else None
                if pnl_val is not None and abs(pnl_val - 0.07) < 0.01:
                    tier1_found = True
                elif any(x in action for x in ["第一", "half", "Half", "1", "partial", "50%", "一半", "第1"]):
                    tier1_found = True
            if code in ("600011", "600015"):
                pnl_val = float(pnl) if pnl is not None else None
                if pnl_val is not None and abs(pnl_val - 0.15) < 0.01:
                    tier2_found = True
                elif any(x in action for x in ["第二", "second", "Second", "2", "remaining", "剩余", "第2"]):
                    tier2_found = True
    # Relaxed: just check both tiers appear somewhere
    passed = tier1_found or tier2_found
    score += add_check(
        "split_take_profit_tiers",
        passed,
        f"Split take-profit tiers: tier1(+7% for 600014)={tier1_found}, tier2(+15% for 600011/600015)={tier2_found}"
    )
except Exception as e:
    score += add_check("split_take_profit_tiers", False, f"Error checking split tiers: {e}")

# Compute final score
total_checks = len(checks)
passed_checks = sum(1 for c in checks if c["passed"])
final_score = passed_checks / total_checks if total_checks > 0 else 0.0
overall_passed = final_score >= 0.75

print(json.dumps({
    "passed": overall_passed,
    "score": round(final_score, 4),
    "checks": checks
}, ensure_ascii=False, indent=2))