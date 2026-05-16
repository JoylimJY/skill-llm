import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Locate the output file ────────────────────────────────────────────────
# Agent is asked to produce: trading_plan_20260715.json
target_files = list(Path(workspace).rglob("trading_plan_20260715.json"))

if not target_files:
    add_check("file_exists", False, "trading_plan_20260715.json not found anywhere in workspace.")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)

plan_path = target_files[0]
add_check("file_exists", True, f"Found at {plan_path}")

try:
    import json as _json
    with open(plan_path, encoding="utf-8") as f:
        plan = _json.load(f)
except Exception as e:
    add_check("json_parseable", False, f"JSON parse error: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)

add_check("json_parseable", True, "File is valid JSON.")

# ── CHECK 1: Date ─────────────────────────────────────────────────────────
try:
    date_val = str(plan.get("date", plan.get("日期", "")))
    date_ok = "2026-07-15" in date_val or "20260715" in date_val
    add_check("date_correct", date_ok, f"date field: '{date_val}'")
except Exception as e:
    add_check("date_correct", False, str(e))

# ── CHECK 2: Selected stocks must pass ALL filters ────────────────────────
# Valid stocks must satisfy:
#   (a) 流通市值 50-300亿
#   (b) 换手率 5%-15%
#   (c) 今日涨停 = 是
#   (d) 板块涨停数 ≥ 3
#   (e) 代码不能缺失（空）
#
# Applying to raw data:
# 300123: 85.3亿✓, 8.7%✓, 涨停✓, 5≥3✓ → VALID (创业板 300xx, 强)
# 002456: 420亿✗ (>300) → INVALID
# 300677: 198.6亿✓, 6.3%✓, 涨停✓, 3≥3✓ → VALID (创业板, 强)
# 688111: 950亿✗ → INVALID
# 300859: 42亿✗ (<50) → INVALID
# 000725: 750亿✗ → INVALID
# 300015: 310.5亿✗ (>300) → INVALID
# 301088: 55.2亿✓, 11.3%✓, 涨停✓, 5≥3✓ → VALID (创业板, 强)
# 300124: 180亿✓, 9.1%✓, 涨停✓, 6≥3✓ → VALID (创业板, 强)
# 002594: 6800亿✗ → INVALID
# 300450: 95.8亿✓, 5.5%✓, 涨停✓, 6≥3✓ → VALID (创业板, 强)
# 缺失代码: 代码为空 → INVALID
# 300999: 260亿✓, 13.2%✓, 涨停✓, 2<3 → INVALID (板块涨停数不足)

VALID_CODES = {"300123", "300677", "301088", "300124", "300450"}
INVALID_CODES = {"002456", "688111", "300859", "000725", "300015", "002594", "300999"}

try:
    positions = plan.get("positions", plan.get("持仓计划", plan.get("trade_positions", [])))
    selected_codes = set()
    for p in positions:
        code = str(p.get("code", p.get("代码", p.get("stock_code", "")))).strip()
        if code:
            selected_codes.add(code)

    # No invalid codes included
    invalid_included = selected_codes & INVALID_CODES
    no_invalid = len(invalid_included) == 0
    add_check("no_invalid_stocks", no_invalid,
              f"Selected: {selected_codes}. Invalid included: {invalid_included}")

    # All selected are from valid set
    all_valid = selected_codes.issubset(VALID_CODES)
    add_check("all_selected_are_valid", all_valid,
              f"Selected {selected_codes}, valid pool {VALID_CODES}")

    # At least 1 valid stock selected
    add_check("at_least_one_selected", len(selected_codes) >= 1,
              f"Selected count: {len(selected_codes)}")

except Exception as e:
    add_check("no_invalid_stocks", False, str(e))
    add_check("all_selected_are_valid", False, str(e))
    add_check("at_least_one_selected", False, str(e))

# ── CHECK 3: 创业板 priority (300xx stocks must be in selection if valid ones exist) ──
try:
    chinext_codes = {c for c in selected_codes if c.startswith("300") or c.startswith("301")}
    # At least some 300xx stocks should be present since they dominate the valid pool
    has_chinext = len(chinext_codes) >= 1
    add_check("chinext_priority_respected", has_chinext,
              f"创业板 stocks selected: {chinext_codes}")
except Exception as e:
    add_check("chinext_priority_respected", False, str(e))

# ── CHECK 4: Total capital = 500,000; cash reserve ≥ 50,000 ─────────────
try:
    total_capital = 500000
    total_invested = 0
    for p in positions:
        amt = p.get("amount", p.get("金额", p.get("invest_amount", p.get("投入金额", 0))))
        try:
            total_invested += float(str(amt).replace(",", "").replace("万", "0000").replace("元", ""))
        except:
            pass
    # If amounts are in 万, convert
    # Heuristic: if total_invested < 1000, it's in 万
    if 0 < total_invested < 1000:
        total_invested *= 10000

    cash_reserve = total_capital - total_invested
    reserve_ok = cash_reserve >= 50000
    add_check("cash_reserve_50k", reserve_ok,
              f"Total invested: {total_invested}, Cash reserve: {cash_reserve} (need ≥50000)")
except Exception as e:
    add_check("cash_reserve_50k", False, str(e))

# ── CHECK 5: Single stock ≤ 50% = ≤ 250,000 ──────────────────────────────
try:
    single_cap_ok = True
    details = []
    for p in positions:
        code = str(p.get("code", p.get("代码", p.get("stock_code", "")))).strip()
        amt = p.get("amount", p.get("金额", p.get("invest_amount", p.get("投入金额", 0))))
        try:
            amt_val = float(str(amt).replace(",", "").replace("万", "").replace("元", ""))
            if 0 < amt_val < 1000:
                amt_val *= 10000
        except:
            amt_val = 0
        if amt_val > 250000:
            single_cap_ok = False
            details.append(f"{code}:{amt_val}")
    add_check("single_stock_cap_50pct", single_cap_ok,
              f"Violations: {details}" if details else "All within 50% cap")
except Exception as e:
    add_check("single_stock_cap_50pct", False, str(e))

# ── CHECK 6: Stop-loss = buy_price * 0.95 (±0.5% tolerance) ─────────────
try:
    sl_ok = True
    sl_details = []
    for p in positions:
        buy_price = p.get("buy_price", p.get("买入价", p.get("entry_price", None)))
        stop_loss = p.get("stop_loss", p.get("止损价", p.get("stop_loss_price", None)))
        code = str(p.get("code", p.get("代码", "?"))).strip()
        if buy_price is not None and stop_loss is not None:
            try:
                bp = float(str(buy_price).replace(",", ""))
                sl = float(str(stop_loss).replace(",", ""))
                expected = bp * 0.95
                # Allow ±0.5% tolerance
                if abs(sl - expected) / expected > 0.005:
                    sl_ok = False
                    sl_details.append(f"{code}: buy={bp}, stop={sl}, expected≈{expected:.2f}")
            except:
                pass
    add_check("stop_loss_5pct", sl_ok,
              f"Violations: {sl_details}" if sl_details else "All stop-losses correct at -5%")
except Exception as e:
    add_check("stop_loss_5pct", False, str(e))

# ── CHECK 7: Buy-point mode is correctly labeled ─────────────────────────
try:
    VALID_MODES = {"首板打板", "二板确认", "分歧转一致"}
    mode_ok = True
    mode_details = []
    for p in positions:
        mode = str(p.get("buy_mode", p.get("买点类型", p.get("entry_mode", "")))).strip()
        if mode not in VALID_MODES:
            mode_ok = False
            mode_details.append(f"code={p.get('code', p.get('代码', '?'))}: '{mode}'")
    add_check("buy_mode_valid", mode_ok,
              f"Invalid modes: {mode_details}" if mode_details else "All buy modes are valid.")
except Exception as e:
    add_check("buy_mode_valid", False, str(e))

# ── CHECK 8: Trade log entries present and use the correct template fields ─
try:
    log_entries = plan.get("trade_log", plan.get("交易日志", plan.get("logs", [])))
    required_fields_cn = {"日期", "标的", "买入价", "卖出价", "盈亏", "买卖理由", "复盘总结"}
    required_fields_en = {"date", "stock", "buy_price", "sell_price", "pnl", "reason", "review"}

    log_ok = False
    log_detail = "No log entries found."
    if log_entries:
        # Accept either Chinese or English field names
        for entry in log_entries:
            keys = set(str(k) for k in entry.keys())
            if required_fields_cn.issubset(keys) or required_fields_en.issubset(keys):
                log_ok = True
                log_detail = f"Valid log entry found with keys: {keys}"
                break
        if not log_ok:
            log_detail = f"Log entries exist but missing required fields. Keys found: {[set(e.keys()) for e in log_entries]}"
    add_check("trade_log_template", log_ok, log_detail)
except Exception as e:
    add_check("trade_log_template", False, str(e))

# ── CHECK 9: Position tier signal-to-size mapping ─────────────────────────
# Strong signal → up to 50% (250k); Normal → up to 30% (150k); Weak → 10-15% (50-75k)
try:
    tier_ok = True
    tier_details = []
    for p in positions:
        signal = str(p.get("signal", p.get("信号强度", p.get("signal_strength", "")))).strip()
        amt = p.get("amount", p.get("金额", p.get("invest_amount", p.get("投入金额", 0))))
        try:
            amt_val = float(str(amt).replace(",", "").replace("万", "").replace("元", ""))
            if 0 < amt_val < 1000:
                amt_val *= 10000
        except:
            continue
        code = str(p.get("code", p.get("代码", "?"))).strip()
        if signal == "强" and amt_val > 250001:
            tier_ok = False
            tier_details.append(f"{code}: 强信号 but {amt_val} > 250000")
        elif signal == "一般" and amt_val > 150001:
            tier_ok = False
            tier_details.append(f"{code}: 一般信号 but {amt_val} > 150000")
        elif signal == "弱" and (amt_val < 49999 or amt_val > 75001):
            tier_ok = False
            tier_details.append(f"{code}: 弱信号 but {amt_val} not in [50000,75000]")
    add_check("position_tier_correct", tier_ok,
              f"Violations: {tier_details}" if tier_details else "Position tiers correctly applied.")
except Exception as e:
    add_check("position_tier_correct", False, str(e))

# ── Scoring ───────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
overall_passed = score >= 0.75 and checks[0]["passed"] and checks[1]["passed"]

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))