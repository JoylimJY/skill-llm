import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Check 1: Output file exists ───────────────────────────────────────────
    report_candidates = list(workspace.rglob("daily_margin_report.json"))
    file_exists = len(report_candidates) > 0
    total_score += add_check(
        "output_file_exists",
        file_exists,
        f"Found {len(report_candidates)} file(s) named 'daily_margin_report.json'" if file_exists
        else "File 'daily_margin_report.json' not found anywhere in workspace"
    )

    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    report_path = report_candidates[0]

    # ── Check 2: File is valid JSON ────────────────────────────────────────────
    try:
        content = report_path.read_text(encoding="utf-8")
        report = json.loads(content)
        total_score += add_check("valid_json", True, f"Parsed successfully from {report_path}")
    except Exception as e:
        total_score += add_check("valid_json", False, f"JSON parse error: {e}")
        return {
            "passed": False,
            "score": total_score / 7.0,
            "checks": checks
        }

    # ── Check 3: Correct top margin stock identified ───────────────────────────
    # The mock data has 601398.SH (工商银行) with margin_balance=15800000000
    # The agent MUST call --all to get the full dataset, then find the max
    expected_symbol = "601398.SH"
    
    found_symbol = None
    # Accept various key names the agent might use
    for key in ["symbol", "stock_symbol", "top_symbol", "stock_code", "code"]:
        if key in report and isinstance(report.get(key), str):
            found_symbol = report[key]
            break
    
    # Also search nested structures
    if found_symbol is None:
        def search_value(obj, depth=0):
            if depth > 5:
                return None
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str) and expected_symbol in v:
                        return v
                    result = search_value(v, depth+1)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = search_value(item, depth+1)
                    if result:
                        return result
            return None
        found_symbol = search_value(report)

    symbol_correct = found_symbol is not None and expected_symbol in str(found_symbol)
    total_score += add_check(
        "correct_top_margin_stock",
        symbol_correct,
        f"Expected top margin stock: {expected_symbol}. Found in report: {found_symbol}. "
        f"Note: The correct stock is 工商银行(601398.SH) with margin_balance=15,800,000,000, "
        f"NOT 招商银行(600036.SH) which appears in distractor files.",
        weight=2.0
    )

    # ── Check 4: Margin balance value is present and correct ──────────────────
    expected_balance = 15800000000
    found_balance = None
    
    def find_numeric(obj, target, tolerance=0.01, depth=0):
        if depth > 5:
            return None
        if isinstance(obj, (int, float)):
            if abs(obj - target) / target < tolerance:
                return obj
        elif isinstance(obj, dict):
            for v in obj.values():
                result = find_numeric(v, target, tolerance, depth+1)
                if result is not None:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = find_numeric(item, target, tolerance, depth+1)
                if result is not None:
                    return result
        return None

    found_balance = find_numeric(report, expected_balance)
    balance_present = found_balance is not None
    total_score += add_check(
        "margin_balance_present",
        balance_present,
        f"Expected margin_balance ~{expected_balance}. Found: {found_balance}",
        weight=1.0
    )

    # ── Check 5: PE ratio (pe_ttm) is present and correct ─────────────────────
    # Mock returns pe_ttm=5.42 for 601398.SH
    expected_pe = 5.42
    found_pe = find_numeric(report, expected_pe, tolerance=0.05)
    pe_present = found_pe is not None
    total_score += add_check(
        "pe_ttm_present",
        pe_present,
        f"Expected pe_ttm ~{expected_pe} for 601398.SH. Found: {found_pe}. "
        f"This value comes from stock-security-info sub-skill using https://ftai.chat domain.",
        weight=2.0
    )

    # ── Check 6: Trade date field present ─────────────────────────────────────
    # get-nth-trade-date returns {"nth_trade_date": "2025-01-08"}
    expected_date = "2025-01-08"
    date_str = json.dumps(report)
    date_present = expected_date in date_str
    total_score += add_check(
        "trade_date_present",
        date_present,
        f"Expected trade date {expected_date} from get-nth-trade-date sub-skill. "
        f"Present in report: {date_present}",
        weight=1.0
    )

    # ── Check 7: Report has meaningful structure (not just raw API dump) ───────
    is_dict = isinstance(report, dict)
    has_multiple_fields = is_dict and len(report) >= 2
    total_score += add_check(
        "report_structure_valid",
        has_multiple_fields,
        f"Report is a dict with {len(report) if is_dict else 'N/A'} top-level fields. "
        f"Expected a structured summary, not a raw array or empty object.",
        weight=0.5
    )

    # ── Final scoring ──────────────────────────────────────────────────────────
    max_score = 1.0 + 2.0 + 1.0 + 2.0 + 1.0 + 0.5  # = 7.5
    normalized = round(total_score / max_score, 4)
    
    # Must pass checks 3 and 5 (correct stock + PE) to be considered passing
    critical_checks = [c for c in checks if c["name"] in ("correct_top_margin_stock", "pe_ttm_present")]
    critical_passed = all(c["passed"] for c in critical_checks)
    
    passed = critical_passed and normalized >= 0.7

    return {
        "passed": passed,
        "score": normalized,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))