import sys
import json
import csv
import os
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)

def run_eval(workspace):
    checks = []
    passed_all = True

    # ── Find portfolio_report.json ─────────────────────────────────────
    report_candidates = list(Path(workspace).rglob("portfolio_report.json"))
    
    if not report_candidates:
        checks.append({
            "name": "report_file_exists",
            "passed": False,
            "detail": "portfolio_report.json not found anywhere in workspace"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    report_path = report_candidates[0]
    checks.append({
        "name": "report_file_exists",
        "passed": True,
        "detail": f"Found at {report_path}"
    })

    # ── Load report ────────────────────────────────────────────────────
    report, err = load_json_safe(report_path)
    if report is None:
        checks.append({
            "name": "report_is_valid_json",
            "passed": False,
            "detail": f"JSON parse error: {err}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({
        "name": "report_is_valid_json",
        "passed": True,
        "detail": "Valid JSON"
    })

    # ── Load portfolio.csv to know expected identifiers ────────────────
    portfolio_path = os.path.join(workspace, "portfolio.csv")
    try:
        expected_entries = []
        with open(portfolio_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                expected_entries.append({
                    "identifier": row["identifier"].strip(),
                    "shares": int(row["shares"])
                })
    except Exception as e:
        checks.append({
            "name": "portfolio_csv_readable",
            "passed": False,
            "detail": f"Could not read portfolio.csv: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "portfolio_csv_readable",
        "passed": True,
        "detail": f"Read {len(expected_entries)} entries from portfolio.csv"
    })

    # ── Check report has a top-level list or dict with stock entries ───
    # Accept either: {"stocks": [...]} or a list directly
    stock_entries = None
    if isinstance(report, list):
        stock_entries = report
    elif isinstance(report, dict):
        # Try common key names
        for key in ["stocks", "portfolio", "holdings", "entries", "data", "results"]:
            if key in report and isinstance(report[key], list):
                stock_entries = report[key]
                break
        if stock_entries is None:
            # Maybe the dict keys are identifiers
            # Check if values are dicts with stock data
            first_val = next(iter(report.values()), None)
            if isinstance(first_val, dict) and "price" in first_val:
                stock_entries = list(report.values())

    has_stock_list = stock_entries is not None and len(stock_entries) > 0
    checks.append({
        "name": "report_has_stock_entries",
        "passed": has_stock_list,
        "detail": f"Found {len(stock_entries) if stock_entries else 0} stock entries in report"
    })
    if not has_stock_list:
        passed_all = False

    # ── Check coverage: all 5 portfolio identifiers are represented ────
    if stock_entries:
        expected_ids = {e["identifier"].lower() for e in expected_entries}
        # Also add known code equivalents
        # We'll check by looking at 'name', 'code', or an 'identifier' field in each entry
        found_ids = set()
        for entry in stock_entries:
            if not isinstance(entry, dict):
                continue
            for field in ["name", "code", "identifier", "symbol", "ticker"]:
                val = str(entry.get(field, "")).strip().lower()
                if val:
                    found_ids.add(val)

        # The portfolio has 5 entries; we need at least 4 represented 
        # (USD may appear as exchange rate with code like "USD")
        expected_count = len(expected_entries)  # 5
        coverage_count = 0
        for exp in expected_entries:
            eid = exp["identifier"].lower()
            if eid in found_ids:
                coverage_count += 1
            else:
                # Partial match: check if any found_id contains eid or vice versa
                for fid in found_ids:
                    if eid in fid or fid in eid or eid[:4] in fid:
                        coverage_count += 1
                        break

        coverage_ok = coverage_count >= 4  # allow 1 miss (e.g., USD might be filtered)
        checks.append({
            "name": "portfolio_coverage",
            "passed": coverage_ok,
            "detail": f"Matched {coverage_count}/{expected_count} portfolio entries. Found ids: {list(found_ids)[:10]}"
        })
        if not coverage_ok:
            passed_all = False

    # ── Check NXT fields are present and numeric in at least one entry ─
    nxt_fields_present = False
    nxt_numeric_ok = False
    divergence_present = False

    if stock_entries:
        nxt_entries_count = 0
        divergence_entries_count = 0
        for entry in stock_entries:
            if not isinstance(entry, dict):
                continue
            has_nxt = "nxtPrice" in entry or "nxt_price" in entry or "nextrade_price" in entry
            if has_nxt:
                nxt_entries_count += 1
                # Check numeric
                nxt_val = entry.get("nxtPrice") or entry.get("nxt_price") or entry.get("nextrade_price")
                if nxt_val is not None and isinstance(nxt_val, (int, float)):
                    nxt_numeric_ok = True

            # Check for divergence field
            has_div = any(k for k in entry.keys() if "diverg" in k.lower() or "nxt_diff" in k.lower() 
                         or "nxt_vs" in k.lower() or "off_hours" in k.lower() or "ats" in k.lower()
                         or "difference" in k.lower() or "delta" in k.lower() or "spread" in k.lower())
            if has_div:
                divergence_entries_count += 1

        nxt_fields_present = nxt_entries_count >= 2  # at least 2 domestic stocks should have NXT
        divergence_present = divergence_entries_count >= 1

        checks.append({
            "name": "nxt_fields_present",
            "passed": nxt_fields_present,
            "detail": f"{nxt_entries_count} entries contain NXT price fields"
        })
        checks.append({
            "name": "nxt_values_are_numeric",
            "passed": nxt_numeric_ok,
            "detail": "At least one NXT price value is a valid number"
        })
        checks.append({
            "name": "nxt_divergence_computed",
            "passed": divergence_present,
            "detail": f"{divergence_entries_count} entries contain NXT vs regular price divergence/delta/spread field"
        })

        if not nxt_fields_present:
            passed_all = False
        if not nxt_numeric_ok:
            passed_all = False
        if not divergence_present:
            passed_all = False

    # ── Check shares and market_value fields ──────────────────────────
    value_fields_present = False
    if stock_entries:
        value_count = 0
        for entry in stock_entries:
            if not isinstance(entry, dict):
                continue
            has_shares = any(k for k in entry.keys() if "share" in k.lower() or "qty" in k.lower() 
                            or "quantity" in k.lower() or "holding" in k.lower() or "position" in k.lower())
            has_value = any(k for k in entry.keys() if "value" in k.lower() or "worth" in k.lower()
                           or "market_val" in k.lower() or "total" in k.lower())
            if has_shares or has_value:
                value_count += 1
        value_fields_present = value_count >= 3
        checks.append({
            "name": "shares_and_value_fields",
            "passed": value_fields_present,
            "detail": f"{value_count} entries contain shares/value tracking fields"
        })
        if not value_fields_present:
            passed_all = False

    # ── Check currency field is present ───────────────────────────────
    currency_present = False
    if stock_entries:
        cur_count = sum(1 for e in stock_entries 
                       if isinstance(e, dict) and "currency" in e and e["currency"] in ["KRW", "USD", "JPY", "EUR", "GBP"])
        currency_present = cur_count >= 2
        checks.append({
            "name": "currency_field_present",
            "passed": currency_present,
            "detail": f"{cur_count} entries have a valid currency field"
        })
        if not currency_present:
            passed_all = False

    # ── Compute overall score ─────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    final_pass = all(c["passed"] for c in checks)

    return {
        "passed": final_pass,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(ws)
    print(json.dumps(result, ensure_ascii=False, indent=2))