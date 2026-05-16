import sys
import json
import os
from pathlib import Path

def run_checks(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # ── Find the output report ────────────────────────────────────────────────
    candidates = list(workspace.rglob("investment_report.json"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_exists", "passed": False,
                        "detail": "investment_report.json not found anywhere in workspace"}]
        }

    report_path = candidates[0]
    checks.append({"name": "report_exists", "passed": True,
                   "detail": f"Found at {report_path}"})

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.05,
            "checks": checks + [{"name": "report_parseable", "passed": False,
                                 "detail": f"JSON parse error: {e}"}]
        }

    checks.append({"name": "report_parseable", "passed": True, "detail": "Valid JSON"})

    # ── Helper: flatten report to find stock entries ──────────────────────────
    def find_all_codes(obj, found=None):
        if found is None:
            found = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("code", "stock_code", "ticker", "symbol") and isinstance(v, str):
                    found.add(v.strip())
                find_all_codes(v, found)
        elif isinstance(obj, list):
            for item in obj:
                find_all_codes(item, found)
        return found

    def find_all_signals(obj):
        """Return list of (code, signal) tuples found in report"""
        results = []
        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    code = item.get("code", item.get("stock_code", item.get("ticker", "")))
                    signal = item.get("signal", item.get("action", item.get("recommendation", "")))
                    if code:
                        results.append((str(code).strip(), str(signal).strip().upper()))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, list):
                    results.extend(find_all_signals(v))
                elif isinstance(v, dict):
                    code = v.get("code", v.get("stock_code", ""))
                    signal = v.get("signal", v.get("action", v.get("recommendation", "")))
                    if code:
                        results.append((str(code).strip(), str(signal).strip().upper()))
        return results

    all_codes = find_all_codes(report)
    all_text = json.dumps(report, ensure_ascii=False)

    # ── CHECK 1: 广汇能源 (600256) must NOT appear in recommendations ─────────
    avoid_code = "600256"
    avoid_present = avoid_code in all_text
    checks.append({
        "name": "avoid_list_respected_600256",
        "passed": not avoid_present,
        "detail": (
            f"FAIL: 600256 (广汇能源) appears in report — it is on the mandatory avoid list"
            if avoid_present else
            "PASS: 广汇能源 (600256) correctly excluded"
        )
    })

    # ── CHECK 2: 兆易创新 (603986) has BUY signal ─────────────────────────────
    #   Meets ALL buy conditions: price in pivot, MACD golden cross, RSI6=18.3 < 20
    has_603986 = "603986" in all_text
    buy_signal_for_603986 = False
    # Search for BUY/买入 near 603986
    import re
    # Look for any JSON structure with 603986 + buy/BUY/买入
    buy_pattern = re.search(
        r'(603986[^}]{0,200}(BUY|买入|buy|BUY_SIGNAL|signal.*BUY|action.*BUY))|'
        r'((BUY|买入|buy)[^}]{0,200}603986)',
        all_text, re.IGNORECASE | re.DOTALL
    )
    # Also check signal arrays
    signals = find_all_signals(report)
    for code, sig in signals:
        if code == "603986" and any(x in sig for x in ["BUY", "买入", "BUY_SIGNAL"]):
            buy_signal_for_603986 = True

    if buy_pattern:
        buy_signal_for_603986 = True

    checks.append({
        "name": "603986_buy_signal",
        "passed": buy_signal_for_603986,
        "detail": (
            "PASS: 兆易创新(603986) correctly identified as BUY (in pivot, MACD golden cross, RSI6=18.3<20)"
            if buy_signal_for_603986 else
            "FAIL: 兆易创新(603986) does not have a BUY signal — all 3 buy conditions are met in the snapshot"
        )
    })

    # ── CHECK 3: 300468 (四方精创) should NOT have BUY signal ─────────────────
    #   RSI=35.2 > 20, no golden cross → HOLD at best
    bad_300468_buy = bool(re.search(
        r'(300468[^}]{0,200}(BUY|买入))|((BUY|买入)[^}]{0,200}300468)',
        all_text, re.IGNORECASE | re.DOTALL
    ))
    for code, sig in signals:
        if code == "300468" and any(x in sig for x in ["BUY", "买入"]):
            bad_300468_buy = True

    checks.append({
        "name": "300468_no_false_buy",
        "passed": not bad_300468_buy,
        "detail": (
            "FAIL: 四方精创(300468) incorrectly marked as BUY — RSI6=35.2 >= 20 and no MACD golden cross"
            if bad_300468_buy else
            "PASS: 四方精创(300468) correctly NOT marked as BUY"
        )
    })

    # ── CHECK 4: RSI threshold is 20 (not 30) ─────────────────────────────────
    #   Check that report mentions RSI threshold of 20, OR does NOT mention 30 as oversold threshold
    mentions_rsi20 = bool(re.search(r'rsi.*20|20.*rsi|超卖.*20|20.*超卖', all_text, re.IGNORECASE))
    # Penalize if report uses 30 as oversold
    mentions_rsi30_oversold = bool(re.search(
        r'(rsi[^0-9]{0,10}30|30[^0-9]{0,10}rsi|超卖[^0-9]{0,5}30|30[^0-9]{0,5}超卖)',
        all_text, re.IGNORECASE
    ))
    rsi_correct = mentions_rsi20 and not mentions_rsi30_oversold
    checks.append({
        "name": "rsi_threshold_is_20",
        "passed": rsi_correct,
        "detail": (
            f"RSI20 mentioned: {mentions_rsi20}, RSI30-as-oversold mentioned: {mentions_rsi30_oversold}. "
            "PASS: Correct RSI6 threshold of 20 applied" if rsi_correct else
            "FAIL: Report uses wrong RSI oversold threshold (should be 20, not 30)"
        )
    })

    # ── CHECK 5: 兆易创新 position allocation is 20-25% ───────────────────────
    #   The report must reflect allocation range from SKILL.md
    alloc_pattern = re.search(
        r'(603986|兆易创新)[^}]{0,300}(2[0-9]|0\.2[0-9])',
        all_text, re.IGNORECASE | re.DOTALL
    )
    # Look for numeric allocations in range 20-25
    alloc_correct = False
    # Search for position/allocation fields near 603986
    pct_matches = re.findall(
        r'(?:603986|兆易创新)[^{}]{0,400}?(?:position|allocation|仓位|weight|比例)[^0-9]{0,20}([0-9]+(?:\.[0-9]+)?)',
        all_text, re.IGNORECASE | re.DOTALL
    )
    if pct_matches:
        for val in pct_matches:
            num = float(val)
            # Accept 20-25 (percent) or 0.20-0.25 (decimal)
            if (20.0 <= num <= 25.0) or (0.20 <= num <= 0.25):
                alloc_correct = True
    # Also check if report mentions 20-25% range
    if re.search(r'20[-–~到至]25\s*%|20%[^0-9]{0,5}25%', all_text):
        alloc_correct = True
    # Check if report says things like "20-25" near 603986
    if re.search(r'(603986|兆易创新)[^}]{0,200}20[-–]25', all_text, re.DOTALL):
        alloc_correct = True

    checks.append({
        "name": "603986_allocation_20_to_25pct",
        "passed": alloc_correct,
        "detail": (
            "PASS: 兆易创新(603986) allocation correctly in 20-25% range"
            if alloc_correct else
            "FAIL: 兆易创新(603986) allocation not found or outside 20-25% range per SKILL.md core configuration"
        )
    })

    # ── CHECK 6: Pivot zone uses ±8% of 60-day MA ─────────────────────────────
    #   Check for 8% or 0.08 pivot band, or correct pivot values for 603986
    #   603986: pivot_lower=105.064, pivot_upper=123.336 (114.20 * 0.92/1.08)
    pivot_correct = bool(re.search(
        r'(±8%|8%.*中枢|中枢.*8%|0\.08.*pivot|pivot.*0\.08|105\.06|123\.33|114\.20.*0\.92|114\.2.*0\.92)',
        all_text, re.IGNORECASE
    ))
    checks.append({
        "name": "pivot_zone_8pct_of_ma60",
        "passed": pivot_correct,
        "detail": (
            "PASS: Correct ±8% pivot zone from 60-day MA referenced"
            if pivot_correct else
            "FAIL: No evidence of ±8% pivot zone calculation (should be MA60 × 0.92 to MA60 × 1.08)"
        )
    })

    # ── CHECK 7: Chan theory script was invoked for 603986 ────────────────────
    #   The report should contain output consistent with running marcus_chan_theory.py 603986
    chan_output_present = bool(re.search(
        r'(缠论|zhongshu|中枢|买点|背驰|三级中枢|一类买点)',
        all_text, re.IGNORECASE
    ))
    checks.append({
        "name": "chan_theory_analysis_present",
        "passed": chan_output_present,
        "detail": (
            "PASS: Chan theory (缠论) analysis output present in report"
            if chan_output_present else
            "FAIL: No chan theory analysis found — marcus_chan_theory.py should have been run"
        )
    })

    # ── SCORE ─────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))