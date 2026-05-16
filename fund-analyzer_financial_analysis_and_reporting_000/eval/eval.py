import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    max_score = 1.0

    # --- Find the report file ---
    report_path = None
    candidates = list(Path(workspace_dir).rglob("equity_fund_report.json"))
    if not candidates:
        # also try top-level workspace
        direct = Path(workspace_dir) / "equity_fund_report.json"
        if direct.exists():
            candidates = [direct]

    if not candidates:
        checks.append({
            "name": "report_file_exists",
            "passed": False,
            "detail": "equity_fund_report.json not found anywhere in workspace"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = candidates[0]
    checks.append({
        "name": "report_file_exists",
        "passed": True,
        "detail": f"Found report at {report_path}"
    })

    # --- Parse JSON ---
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({
            "name": "report_valid_json",
            "passed": False,
            "detail": f"Failed to parse JSON: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "report_valid_json",
        "passed": True,
        "detail": "JSON parsed successfully"
    })

    # --- Check top-level structure: must have a list of funds ---
    funds_list = None
    # Accept either root-level list or {"funds": [...]} or {"results": [...]}
    if isinstance(report, list):
        funds_list = report
    elif isinstance(report, dict):
        for key in ["funds", "results", "data", "top_funds"]:
            if key in report and isinstance(report[key], list):
                funds_list = report[key]
                break
        if funds_list is None:
            # maybe the report has fund codes as keys
            # try to find any list value
            for v in report.values():
                if isinstance(v, list) and len(v) >= 1:
                    funds_list = v
                    break

    if funds_list is None or len(funds_list) == 0:
        checks.append({
            "name": "report_has_fund_list",
            "passed": False,
            "detail": "Could not find a list of funds in the report"
        })
        return {"passed": False, "score": 0.05, "checks": checks}

    checks.append({
        "name": "report_has_fund_list",
        "passed": True,
        "detail": f"Found fund list with {len(funds_list)} entries"
    })

    # --- Check exactly 3 funds from screener results ---
    expected_codes = {"110011", "161039", "003095"}

    found_codes = set()
    for item in funds_list:
        if isinstance(item, dict):
            # look for fund_code field
            for key in ["fund_code", "code", "基金代码"]:
                if key in item:
                    found_codes.add(str(item[key]).strip())
                    break

    correct_codes = expected_codes & found_codes
    all_three_present = expected_codes.issubset(found_codes)

    checks.append({
        "name": "screener_top3_equity_funds_present",
        "passed": all_three_present,
        "detail": f"Expected codes {expected_codes}, found {found_codes}. Matched: {correct_codes}"
    })

    # --- Check NAV data is included for each fund ---
    nav_fields = ["latest_nav", "最新净值", "nav", "unit_nav"]
    nav_present_count = 0
    for item in funds_list:
        if isinstance(item, dict):
            has_nav = any(f in item for f in nav_fields)
            # Also check nested nav_info or similar
            if not has_nav:
                for v in item.values():
                    if isinstance(v, dict) and any(f in v for f in nav_fields):
                        has_nav = True
                        break
            if has_nav:
                nav_present_count += 1

    nav_check_passed = nav_present_count >= 3
    checks.append({
        "name": "nav_data_included",
        "passed": nav_check_passed,
        "detail": f"{nav_present_count}/3 funds have NAV data"
    })

    # --- Check that specific NAV values match mock data ---
    expected_navs = {"110011": "2.4580", "161039": "1.3450", "003095": "3.1020"}
    nav_values_correct = 0
    for item in funds_list:
        if not isinstance(item, dict):
            continue
        code = None
        for key in ["fund_code", "code", "基金代码"]:
            if key in item:
                code = str(item[key]).strip()
                break
        if code not in expected_navs:
            continue
        expected_nav = expected_navs[code]
        # search for the nav value anywhere in this item
        item_str = json.dumps(item, ensure_ascii=False)
        if expected_nav in item_str:
            nav_values_correct += 1

    checks.append({
        "name": "nav_values_correct",
        "passed": nav_values_correct >= 3,
        "detail": f"{nav_values_correct}/3 funds have correct NAV values from query_fund_nav.py"
    })

    # --- Check holdings data is included ---
    holding_fields = ["top10_holdings", "holdings", "持仓", "top_holdings", "sector_distribution"]
    holdings_present_count = 0
    for item in funds_list:
        if isinstance(item, dict):
            has_holdings = any(f in item for f in holding_fields)
            if not has_holdings:
                # check nested
                for v in item.values():
                    if isinstance(v, dict) and any(f in v for f in holding_fields):
                        has_holdings = True
                        break
                    if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                        # could be holdings list directly
                        sub = v[0]
                        if any(k in sub for k in ["stock", "股票", "code", "weight"]):
                            has_holdings = True
                            break
            if has_holdings:
                holdings_present_count += 1

    holdings_check_passed = holdings_present_count >= 3
    checks.append({
        "name": "holdings_data_included",
        "passed": holdings_check_passed,
        "detail": f"{holdings_present_count}/3 funds have holdings data"
    })

    # --- Check specific holdings content (宁德时代 in 110011) ---
    holdings_content_correct = 0
    expected_holdings_evidence = {
        "110011": "宁德时代",
        "161039": "中国神华",
        "003095": "药明康德"
    }
    for item in funds_list:
        if not isinstance(item, dict):
            continue
        code = None
        for key in ["fund_code", "code", "基金代码"]:
            if key in item:
                code = str(item[key]).strip()
                break
        if code not in expected_holdings_evidence:
            continue
        evidence = expected_holdings_evidence[code]
        item_str = json.dumps(item, ensure_ascii=False)
        if evidence in item_str:
            holdings_content_correct += 1

    checks.append({
        "name": "holdings_content_correct",
        "passed": holdings_content_correct >= 3,
        "detail": f"{holdings_content_correct}/3 funds have correct holdings content from query_fund_holding.py"
    })

    # --- Check history/risk data is included ---
    history_fields = ["sharpe_ratio", "max_drawdown", "nav_curve", "peer_rank", "return_1y", "return_3y", "近1年收益", "历史"]
    history_present_count = 0
    for item in funds_list:
        if isinstance(item, dict):
            has_history = any(f in item for f in history_fields)
            if not has_history:
                item_str = json.dumps(item, ensure_ascii=False)
                # check for any of the history indicators
                if any(f in item_str for f in ["sharpe", "drawdown", "nav_curve", "peer_rank"]):
                    has_history = True
            if has_history:
                history_present_count += 1

    history_check_passed = history_present_count >= 3
    checks.append({
        "name": "history_risk_data_included",
        "passed": history_check_passed,
        "detail": f"{history_present_count}/3 funds have history/risk data (sharpe, drawdown, nav_curve, etc.)"
    })

    # --- Check correct screener parameters were used (股票型 + 近1年 implied by codes) ---
    # The expected codes match the 近1年 股票型 top3 from mock screener
    # If all 3 codes match exactly {110011, 161039, 003095} it implies correct screener params
    screener_params_correct = expected_codes == found_codes or expected_codes.issubset(found_codes)
    checks.append({
        "name": "correct_screener_params_inferred",
        "passed": screener_params_correct,
        "detail": f"Funds {found_codes} match expected screener output for --rank 近1年 --type 股票型 --top 3"
    })

    # --- Final scoring ---
    check_weights = {
        "report_file_exists": 0.05,
        "report_valid_json": 0.05,
        "report_has_fund_list": 0.05,
        "screener_top3_equity_funds_present": 0.15,
        "nav_data_included": 0.10,
        "nav_values_correct": 0.15,
        "holdings_data_included": 0.10,
        "holdings_content_correct": 0.15,
        "history_risk_data_included": 0.10,
        "correct_screener_params_inferred": 0.10,
    }

    score = 0.0
    for check in checks:
        w = check_weights.get(check["name"], 0.0)
        if check["passed"]:
            score += w

    all_critical = (
        all(c["passed"] for c in checks if c["name"] in [
            "report_file_exists",
            "report_valid_json",
            "report_has_fund_list",
            "screener_top3_equity_funds_present",
            "nav_values_correct",
            "holdings_content_correct",
        ])
    )

    return {
        "passed": all_critical and score >= 0.75,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))