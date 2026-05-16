import sys
import json
import math
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # ── 1. Find the output file ──────────────────────────────────────────────
    candidates = list(workspace.rglob("semiconductor_analysis.json"))
    # exclude the archive distractor
    candidates = [c for c in candidates if "archive" not in str(c)]
    
    if not candidates:
        add_check("file_exists", False, "semiconductor_analysis.json not found anywhere in workspace")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    add_check("file_exists", True, f"Found at {candidates[0]}")
    fpath = candidates[0]

    # ── 2. Parse JSON ────────────────────────────────────────────────────────
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        add_check("json_parseable", False, f"JSON parse error: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("json_parseable", True, "Valid JSON")

    # ── 3. Top-level structure ───────────────────────────────────────────────
    sector_ok = data.get("sector") == "半导体"
    add_check("sector_field", sector_ok, f"sector = {data.get('sector')!r}")

    has_generated_date = "generated_date" in data and data["generated_date"]
    add_check("generated_date_field", has_generated_date, f"generated_date = {data.get('generated_date')!r}")

    stocks = data.get("stocks")
    stocks_is_list = isinstance(stocks, list)
    add_check("stocks_is_list", stocks_is_list, f"stocks type: {type(stocks)}")
    
    if not stocks_is_list or len(stocks) == 0:
        add_check("stocks_count", False, "stocks array is empty or missing")
        total_passed = sum(c["passed"] for c in checks)
        return {"passed": False, "score": total_passed / len(checks), "checks": checks}

    # ── 4. All 5 sector constituents are present ─────────────────────────────
    expected_codes = {"002049", "300316", "688012", "002371", "603501"}
    found_codes = {str(s.get("code", "")).strip() for s in stocks}
    all_present = expected_codes.issubset(found_codes)
    add_check("all_5_stocks_present", all_present, 
              f"Expected {expected_codes}, found {found_codes}")

    # ── 5. Required fields in each stock entry ───────────────────────────────
    required_fields = {"code", "name", "annualized_return", "max_drawdown", "latest_revenue", "composite_rank"}
    fields_ok = all(required_fields.issubset(set(s.keys())) for s in stocks)
    add_check("required_fields_present", fields_ok,
              f"Missing fields in some entries: " + 
              str([required_fields - set(s.keys()) for s in stocks if required_fields - set(s.keys())]))

    # ── 6. Verify correct akshare parameters were used (via data values) ─────
    # The mock returns data ONLY for adjust="qfq" and indicator="按报告期"
    # If wrong params used, hist/financial DataFrames would be empty → missing/zero values
    
    # All stocks should have non-zero annualized_return (empty hist → no data to compute)
    nonzero_returns = all(
        s.get("annualized_return") is not None and s.get("annualized_return") != 0
        for s in stocks
    )
    add_check("nonzero_annualized_returns", nonzero_returns,
              "All stocks must have non-zero annualized_return (requires adjust='qfq')")
    
    # All stocks should have non-zero revenue (empty financial → no data)
    nonzero_revenue = all(
        s.get("latest_revenue") is not None and float(s.get("latest_revenue", 0)) > 0
        for s in stocks
    )
    add_check("nonzero_latest_revenue", nonzero_revenue,
              "All stocks must have positive latest_revenue (requires indicator='按报告期')")

    # ── 7. Validate numeric ranges (sanity checks) ───────────────────────────
    # annualized_return should be a decimal (not percent) - reasonable range [-1, 5]
    returns_decimal = all(
        isinstance(s.get("annualized_return"), (int, float)) and
        -1.0 <= float(s.get("annualized_return", 0)) <= 10.0
        for s in stocks
    )
    add_check("annualized_return_is_decimal", returns_decimal,
              "annualized_return should be decimal (e.g. 0.15 for 15%), range [-1, 10]")

    # max_drawdown should be negative or zero
    drawdown_negative = all(
        isinstance(s.get("max_drawdown"), (int, float)) and
        float(s.get("max_drawdown", 0)) <= 0
        for s in stocks
    )
    add_check("max_drawdown_is_negative", drawdown_negative,
              "max_drawdown must be ≤ 0 (a loss, expressed as negative decimal)")

    # latest_revenue should be positive float (亿元 scale, reasonable: 5–200)
    revenue_range = all(
        isinstance(s.get("latest_revenue"), (int, float)) and
        1.0 <= float(s.get("latest_revenue", 0)) <= 500.0
        for s in stocks
    )
    add_check("latest_revenue_range_plausible", revenue_range,
              "latest_revenue should be in reasonable 亿元 range [1, 500]")

    # ── 8. composite_rank: integers 1..N, all unique, all present ────────────
    try:
        ranks = [int(s.get("composite_rank", -1)) for s in stocks]
        n = len(stocks)
        ranks_valid = sorted(ranks) == list(range(1, n + 1))
        add_check("composite_rank_valid", ranks_valid,
                  f"Ranks must be 1..{n} unique integers, got {sorted(ranks)}")
    except Exception as e:
        add_check("composite_rank_valid", False, f"Error checking ranks: {e}")

    # ── 9. Rank ordering: verify rank=1 has highest composite score ──────────
    # Composite = 0.6 * annualized_return + 0.4 * (latest_revenue / max_revenue)
    # We check rank ordering is consistent with the formula direction
    try:
        def composite_score(s):
            ar = float(s.get("annualized_return", 0))
            rev = float(s.get("latest_revenue", 0))
            return ar, rev  # just check rank=1 isn't clearly the worst
        
        rank1_stock = next(s for s in stocks if int(s.get("composite_rank", 0)) == 1)
        rank_last = next(s for s in stocks if int(s.get("composite_rank", 0)) == len(stocks))
        
        # Compute raw composite for rank1 vs rank_last
        max_rev = max(float(s.get("latest_revenue", 0)) for s in stocks)
        def raw_composite(s):
            ar = float(s.get("annualized_return", 0))
            rev = float(s.get("latest_revenue", 0))
            return 0.6 * ar + 0.4 * (rev / max_rev if max_rev > 0 else 0)
        
        score1 = raw_composite(rank1_stock)
        score_last = raw_composite(rank_last)
        rank_order_ok = score1 >= score_last
        add_check("rank_order_consistent_with_formula", rank_order_ok,
                  f"Rank1 composite={score1:.4f} should >= rank_last composite={score_last:.4f}")
    except Exception as e:
        add_check("rank_order_consistent_with_formula", False, f"Error: {e}")

    # ── Final Score ──────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(c["passed"] for c in checks)
    score = round(passed_count / total, 4)
    
    # Hard requirements for passing
    hard_required = [
        "file_exists", "json_parseable", "sector_field", "stocks_is_list",
        "all_5_stocks_present", "nonzero_annualized_returns", "nonzero_latest_revenue",
        "composite_rank_valid"
    ]
    hard_passed = all(
        next((c["passed"] for c in checks if c["name"] == r), False)
        for r in hard_required
    )
    
    return {
        "passed": hard_passed and score >= 0.75,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))