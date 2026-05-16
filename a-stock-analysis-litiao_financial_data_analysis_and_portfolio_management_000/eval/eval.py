import sys
import json
import os
from pathlib import Path

def main(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 5

    # ── Check 1: Portfolio file exists at the correct proprietary path ──
    portfolio_path = Path.home() / '.clawdbot' / 'skills' / 'a-stock-analysis' / 'portfolio.json'
    check1 = {"name": "Portfolio file exists at ~/.clawdbot/skills/a-stock-analysis/portfolio.json", "passed": False, "detail": ""}
    try:
        if not portfolio_path.exists():
            check1["detail"] = f"File not found at {portfolio_path}"
        else:
            check1["passed"] = True
            check1["detail"] = f"Found at {portfolio_path}"
            total_score += 1
    except Exception as e:
        check1["detail"] = f"Exception: {e}"
    checks.append(check1)

    # ── Check 2: Portfolio has all 3 stocks with correct cost/qty ──
    check2 = {"name": "Portfolio contains 600036, 002594, 300750 with correct cost and qty", "passed": False, "detail": ""}
    try:
        pf = json.loads(portfolio_path.read_text(encoding='utf-8'))
        expected = {
            '600036': {'cost': 36.50, 'qty': 2000},
            '002594': {'cost': 210.00, 'qty': 500},
            '300750': {'cost': 185.00, 'qty': 300},
        }
        missing = []
        wrong = []
        for code, exp in expected.items():
            if code not in pf:
                missing.append(code)
                continue
            actual_cost = float(pf[code].get('cost', 0))
            actual_qty = int(pf[code].get('qty', 0))
            if abs(actual_cost - exp['cost']) > 0.01:
                wrong.append(f"{code} cost: expected {exp['cost']}, got {actual_cost}")
            if actual_qty != exp['qty']:
                wrong.append(f"{code} qty: expected {exp['qty']}, got {actual_qty}")
        if missing:
            check2["detail"] = f"Missing stocks: {missing}; Wrong: {wrong}"
        elif wrong:
            check2["detail"] = f"Wrong values: {wrong}"
        else:
            check2["passed"] = True
            check2["detail"] = "All 3 positions correct"
            total_score += 1
    except Exception as e:
        check2["detail"] = f"Exception reading portfolio: {e}"
    checks.append(check2)

    # ── Check 3: intraday_analysis_600036.json exists ──
    check3 = {"name": "intraday_analysis_600036.json exists", "passed": False, "detail": ""}
    report_path = None
    try:
        candidates = list(workspace.rglob('intraday_analysis_600036.json'))
        # Also check home dir and common locations
        home_candidates = list(Path.home().rglob('intraday_analysis_600036.json'))
        all_candidates = candidates + home_candidates
        # Also check cwd
        cwd_candidates = list(Path('/').rglob('intraday_analysis_600036.json'))
        all_candidates = list(set(all_candidates + cwd_candidates))
        
        if not all_candidates:
            check3["detail"] = "File intraday_analysis_600036.json not found anywhere"
        else:
            report_path = all_candidates[0]
            check3["passed"] = True
            check3["detail"] = f"Found at {report_path}"
            total_score += 1
    except Exception as e:
        check3["detail"] = f"Exception: {e}"
    checks.append(check3)

    # ── Check 4: Report has valid JSON structure with minute/intraday data ──
    check4 = {"name": "Report contains valid intraday analysis data for 600036", "passed": False, "detail": ""}
    try:
        if report_path is None:
            check4["detail"] = "No report file found (check 3 failed)"
        else:
            content = report_path.read_text(encoding='utf-8')
            data = json.loads(content)
            
            # The report could be structured as {"600036": {...}} or directly as the analysis
            # Look for minute_analysis or distribution data
            def find_distribution(d, depth=0):
                if depth > 5:
                    return None
                if isinstance(d, dict):
                    # Direct distribution key
                    if 'distribution' in d:
                        dist = d['distribution']
                        if isinstance(dist, dict) and all(k in dist for k in ['early_session', 'mid_am', 'mid_pm', 'tail_session']):
                            return dist
                    # minute_analysis wrapper
                    if 'minute_analysis' in d and isinstance(d['minute_analysis'], dict):
                        return find_distribution(d['minute_analysis'], depth+1)
                    # Try all values
                    for v in d.values():
                        result = find_distribution(v, depth+1)
                        if result is not None:
                            return result
                return None
            
            dist = find_distribution(data)
            if dist is None:
                check4["detail"] = f"No valid distribution structure found in JSON. Keys found: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}"
            else:
                # Validate that the 4 required time segments are present
                required_keys = ['early_session', 'mid_am', 'mid_pm', 'tail_session']
                missing_keys = [k for k in required_keys if k not in dist]
                if missing_keys:
                    check4["detail"] = f"Missing time segments: {missing_keys}"
                else:
                    check4["passed"] = True
                    check4["detail"] = f"All 4 time segments present: early={dist['early_session'].get('pct')}%, tail={dist['tail_session'].get('pct')}%"
                    total_score += 1
    except json.JSONDecodeError as e:
        check4["detail"] = f"Invalid JSON in report: {e}"
    except Exception as e:
        check4["detail"] = f"Exception: {e}"
    checks.append(check4)

    # ── Check 5: Report contains signals field (proprietary signal logic) ──
    check5 = {"name": "Report contains main force activity signals for 600036", "passed": False, "detail": ""}
    try:
        if report_path is None:
            check5["detail"] = "No report file found"
        else:
            content = report_path.read_text(encoding='utf-8')
            data = json.loads(content)
            
            def find_signals(d, depth=0):
                if depth > 5:
                    return None
                if isinstance(d, dict):
                    if 'signals' in d and isinstance(d['signals'], list):
                        return d['signals']
                    if 'minute_analysis' in d and isinstance(d['minute_analysis'], dict):
                        return find_signals(d['minute_analysis'], depth+1)
                    for v in d.values():
                        result = find_signals(v, depth+1)
                        if result is not None:
                            return result
                return None
            
            signals = find_signals(data)
            if signals is None:
                check5["detail"] = "No 'signals' field found in report"
            elif not isinstance(signals, list):
                check5["detail"] = f"'signals' is not a list: {signals}"
            else:
                # For 600036, early_pct should be ~43% -> 主力强势介入 signal expected
                signal_text = ' '.join(signals)
                if '主力' in signal_text or '抢筹' in signal_text or '介入' in signal_text:
                    check5["passed"] = True
                    check5["detail"] = f"Valid signals found: {signals}"
                    total_score += 1
                else:
                    check5["detail"] = f"Signals present but no institutional activity signal for 600036 (early volume should trigger '主力强势介入'). Got: {signals}"
    except Exception as e:
        check5["detail"] = f"Exception: {e}"
    checks.append(check5)

    final_score = total_score / max_score
    result = {
        "passed": final_score >= 0.8,
        "score": round(final_score, 2),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == '__main__':
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    main(workspace_dir)