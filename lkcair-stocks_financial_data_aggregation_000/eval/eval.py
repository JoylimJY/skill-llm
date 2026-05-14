import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # --- CHECK 1: Find the output file ---
    report_files = list(workspace.rglob("semiconductor_report.json"))
    # Exclude the old broken attempt
    report_files = [f for f in report_files if "OLD" not in f.name]

    file_found = len(report_files) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found semiconductor_report.json at: {[str(f) for f in report_files]}" if file_found else "semiconductor_report.json not found anywhere in workspace"
    })

    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = report_files[0]

    # --- CHECK 2: File is valid JSON ---
    try:
        with open(report_path, 'r') as f:
            data = json.load(f)
        valid_json = True
        checks.append({
            "name": "valid_json",
            "passed": True,
            "detail": f"File parsed successfully from {report_path}"
        })
    except (json.JSONDecodeError, IOError) as e:
        checks.append({
            "name": "valid_json",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        return {"passed": False, "score": 0.1, "checks": checks}

    # --- CHECK 3: Contains the three semiconductor tickers ---
    report_str = json.dumps(data).upper()
    required_tickers = ["NVDA", "AMD", "INTC"]
    tickers_found = [t for t in required_tickers if t in report_str]
    all_tickers_present = len(tickers_found) == 3
    checks.append({
        "name": "all_three_tickers_present",
        "passed": all_tickers_present,
        "detail": f"Tickers found in report: {tickers_found}. Expected all of: {required_tickers}"
    })
    if all_tickers_present:
        total_score += 0.25

    # --- CHECK 4: Contains comparison data (from compare_stocks or equivalent multi-stock call) ---
    # Look for evidence of comparative data - at minimum a key that implies multi-stock comparison
    comparison_keys = ["comparison", "compare", "stocks", "peers", "sector"]
    has_comparison_section = any(
        k.lower() in json.dumps(data).lower() for k in comparison_keys
    )
    # More strictly: the data should contain multiple ticker entries that aren't just names
    # Check if there are at least 2 separate data blobs with financial info
    def count_financial_entries(obj, depth=0):
        """Count how many distinct objects have financial fields."""
        financial_keywords = ["price", "pe", "ratio", "margin", "revenue", "eps",
                               "market", "cap", "forward", "trailing", "recommend",
                               "buy", "sell", "hold", "target", "52"]
        count = 0
        if isinstance(obj, dict):
            obj_str = json.dumps(obj).lower()
            if any(kw in obj_str for kw in financial_keywords) and depth > 0:
                count += 1
            for v in obj.values():
                count += count_financial_entries(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                count += count_financial_entries(item, depth + 1)
        return count

    financial_data_richness = count_financial_entries(data)
    has_multi_stock_data = financial_data_richness >= 2 or has_comparison_section

    checks.append({
        "name": "contains_comparative_or_multi_stock_data",
        "passed": has_multi_stock_data,
        "detail": f"Financial data richness score: {financial_data_richness}. Comparison section detected: {has_comparison_section}"
    })
    if has_multi_stock_data:
        total_score += 0.20

    # --- CHECK 5: Contains key ratios data ---
    # Must have ratio-like content: P/E, margins, ROE, etc.
    ratio_keywords = ["pe_ratio", "pe", "p/e", "roe", "margin", "gross_margin",
                      "profit_margin", "forward_pe", "trailing_pe", "pricetoearnings",
                      "price_to_earnings", "returnOnEquity", "grossMargins", "profitMargins",
                      "forwardPE", "trailingPE"]
    report_lower = json.dumps(data).lower()
    ratio_hits = [kw for kw in ratio_keywords if kw.lower() in report_lower]
    has_ratios = len(ratio_hits) >= 2

    checks.append({
        "name": "contains_key_ratios_data",
        "passed": has_ratios,
        "detail": f"Ratio keywords found: {ratio_hits[:5]}. Need at least 2 distinct ratio indicators."
    })
    if has_ratios:
        total_score += 0.20

    # --- CHECK 6: Contains analyst recommendation data ---
    # Must have recommendation-like content
    analyst_keywords = ["recommend", "buy", "sell", "hold", "strongbuy", "strong_buy",
                        "analyst", "rating", "upgrade", "downgrade", "target",
                        "strongBuy", "strongSell", "meanRecommendation", "numberOfAnalystOpinions"]
    analyst_hits = [kw for kw in analyst_keywords if kw.lower() in report_lower]
    has_analyst = len(analyst_hits) >= 2

    checks.append({
        "name": "contains_analyst_recommendation_data",
        "passed": has_analyst,
        "detail": f"Analyst keywords found: {analyst_hits[:5]}. Need at least 2 distinct analyst indicators."
    })
    if has_analyst:
        total_score += 0.20

    # --- CHECK 7: Report is not trivially empty or just ticker names ---
    # Minimum substantive content: at least 500 characters
    report_content_len = len(json.dumps(data))
    is_substantive = report_content_len >= 500
    checks.append({
        "name": "report_has_substantive_content",
        "passed": is_substantive,
        "detail": f"Report JSON string length: {report_content_len}. Minimum required: 500 characters."
    })
    if is_substantive:
        total_score += 0.10

    # --- CHECK 8: Data appears to be real fetched data (not placeholder/mocked) ---
    # Detect if the file just contains the broken attempt content or placeholder text
    broken_indicators = ["incomplete", "failed", "placeholder", "todo", "fixme",
                         "error: incomplete", "do not use"]
    is_not_placeholder = not any(ind in report_lower for ind in broken_indicators)
    # Also check it's not just the old broken file copied
    is_not_broken_copy = data.get("error") != "incomplete - missing required fields"

    actually_real = is_not_placeholder and is_not_broken_copy
    checks.append({
        "name": "report_contains_real_fetched_data",
        "passed": actually_real,
        "detail": "Report does not appear to be a placeholder or copy of the broken attempt file." if actually_real else "Report appears to be a placeholder or the broken attempt file."
    })
    if actually_real:
        total_score += 0.05

    # --- FINAL VERDICT ---
    # Must pass: file exists, valid json, all 3 tickers, at least key ratios OR analyst data, substantive
    critical_checks = [
        checks[0]["passed"],  # file exists
        checks[1]["passed"],  # valid json
        checks[2]["passed"],  # all 3 tickers
        checks[4]["passed"] or checks[5]["passed"],  # ratios OR analyst
        checks[6]["passed"],  # substantive
        checks[7]["passed"],  # real data
    ]
    overall_passed = all(critical_checks)

    return {
        "passed": overall_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))