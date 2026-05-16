import sys
import json
import os
import subprocess
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight

# ── Helper: run psql ──────────────────────────────────────────────────────────
env = os.environ.copy()
env.update({
    "PGHOST": "localhost",
    "PGDATABASE": "investage",
    "PGUSER": "investage_user",
    "PGPASSWORD": "investage_pass",
})

def psql_query(sql):
    result = subprocess.run(
        ["psql", "-U", "investage_user", "-d", "investage", "-t", "-c", sql],
        capture_output=True, text=True, env=env
    )
    return result.stdout.strip(), result.returncode

# ── Check 1: stocks table exists with correct schema ─────────────────────────
try:
    out, rc = psql_query(
        "SELECT column_name, data_type, character_maximum_length "
        "FROM information_schema.columns "
        "WHERE table_name='stocks' ORDER BY ordinal_position;"
    )
    if rc != 0 or not out:
        add_check("stocks_table_exists", False, "Table 'stocks' not found or query failed", 1.5)
    else:
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        col_names = [l.split("|")[0].strip() for l in lines]
        expected_cols = {"ticker", "company_name", "sector", "currency"}
        missing = expected_cols - set(col_names)
        if missing:
            add_check("stocks_table_exists", False, f"Missing columns: {missing}", 1.5)
        else:
            # Check currency default — query the default
            default_out, _ = psql_query(
                "SELECT column_default FROM information_schema.columns "
                "WHERE table_name='stocks' AND column_name='currency';"
            )
            has_default = "USD" in default_out
            add_check("stocks_table_exists", True,
                      f"stocks table OK; currency default={'USD' if has_default else 'MISSING'}", 1.5)
except Exception as e:
    add_check("stocks_table_exists", False, f"Exception: {e}", 1.5)

# ── Check 2: holdings table correct DECIMAL precision ─────────────────────────
try:
    out, rc = psql_query(
        "SELECT column_name, numeric_precision, numeric_scale "
        "FROM information_schema.columns "
        "WHERE table_name='holdings' AND column_name IN ('shares','avg_cost') "
        "ORDER BY column_name;"
    )
    if rc != 0 or not out:
        add_check("holdings_decimal_precision", False, "holdings table missing or wrong columns", 1.5)
    else:
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        precision_map = {}
        for l in lines:
            parts = [p.strip() for p in l.split("|")]
            if len(parts) >= 3:
                precision_map[parts[0]] = (parts[1], parts[2])
        
        shares_ok = precision_map.get("shares") == ("15", "4")
        avg_cost_ok = precision_map.get("avg_cost") == ("10", "4")
        
        passed = shares_ok and avg_cost_ok
        detail = f"shares DECIMAL(15,4)={shares_ok}, avg_cost DECIMAL(10,4)={avg_cost_ok}. Raw: {precision_map}"
        add_check("holdings_decimal_precision", passed, detail, 1.5)
except Exception as e:
    add_check("holdings_decimal_precision", False, f"Exception: {e}", 1.5)

# ── Check 3: watchlist table has default status='WATCHING' ───────────────────
try:
    out, rc = psql_query(
        "SELECT column_default FROM information_schema.columns "
        "WHERE table_name='watchlist' AND column_name='status';"
    )
    has_watching = "WATCHING" in out
    add_check("watchlist_default_status", has_watching,
              f"watchlist.status default contains 'WATCHING': {has_watching}. Raw: {out}", 1.0)
except Exception as e:
    add_check("watchlist_default_status", False, f"Exception: {e}", 1.0)

# ── Check 4: all 7 stocks inserted ────────────────────────────────────────────
try:
    out, rc = psql_query("SELECT COUNT(*) FROM stocks;")
    count = int(out.strip()) if out.strip().isdigit() else 0
    passed = count >= 7
    add_check("stocks_populated", passed, f"stocks row count={count}, expected>=7", 1.0)
except Exception as e:
    add_check("stocks_populated", False, f"Exception: {e}", 1.0)

# ── Check 5: holdings has 6 rows (both NVDA lots must be present) ─────────────
try:
    out, rc = psql_query("SELECT COUNT(*) FROM holdings;")
    count = int(out.strip()) if out.strip().isdigit() else 0
    # Check NVDA specifically appears twice
    nvda_out, _ = psql_query("SELECT COUNT(*) FROM holdings WHERE ticker='NVDA';")
    nvda_count = int(nvda_out.strip()) if nvda_out.strip().isdigit() else 0
    passed = count >= 6 and nvda_count == 2
    add_check("holdings_populated_with_duplicates", passed,
              f"holdings total={count} (expected>=6), NVDA rows={nvda_count} (expected=2)", 1.5)
except Exception as e:
    add_check("holdings_populated_with_duplicates", False, f"Exception: {e}", 1.5)

# ── Check 6: watchlist populated ─────────────────────────────────────────────
try:
    out, rc = psql_query("SELECT COUNT(*) FROM watchlist;")
    count = int(out.strip()) if out.strip().isdigit() else 0
    passed = count >= 2
    add_check("watchlist_populated", passed, f"watchlist count={count}, expected>=2", 0.5)
except Exception as e:
    add_check("watchlist_populated", False, f"Exception: {e}", 0.5)

# ── Check 7: portfolio_report.json exists ────────────────────────────────────
report_path = None
try:
    candidates = list(Path(workspace).rglob("portfolio_report.json"))
    if not candidates:
        add_check("report_file_exists", False, "portfolio_report.json not found anywhere in workspace", 2.0)
    else:
        report_path = candidates[0]
        add_check("report_file_exists", True, f"Found at {report_path}", 2.0)
except Exception as e:
    add_check("report_file_exists", False, f"Exception: {e}", 2.0)

# ── Check 8: correct weighted scores ─────────────────────────────────────────
WEIGHTS = {"valuation": 0.30, "trend": 0.25, "macro_sentiment": 0.20, "technical": 0.15, "risk": 0.10}
COMPONENT_SCORES = {
    "NVDA":  {"valuation": 80, "trend": 75, "macro_sentiment": 70, "technical": 85, "risk": 60},
    "AAPL":  {"valuation": 60, "trend": 55, "macro_sentiment": 65, "technical": 50, "risk": 70},
    "MSFT":  {"valuation": 55, "trend": 60, "macro_sentiment": 68, "technical": 58, "risk": 75},
    "JNJ":   {"valuation": 45, "trend": 40, "macro_sentiment": 50, "technical": 38, "risk": 65},
    "BRK-B": {"valuation": 30, "trend": 35, "macro_sentiment": 42, "technical": 28, "risk": 55},
}

def expected_score(ticker):
    comps = COMPONENT_SCORES[ticker]
    return round(sum(comps[dim] * WEIGHTS[dim] for dim in WEIGHTS), 2)

def expected_recommendation(score):
    if score >= 65:
        return "BUY"
    elif score >= 50:
        return "HOLD"
    elif score >= 40:
        return "WATCH"
    else:
        return "SELL"

if report_path:
    try:
        with open(report_path) as f:
            report = json.load(f)
        
        # report should be a list or dict keyed by ticker
        if isinstance(report, list):
            report_dict = {item.get("ticker", item.get("symbol", "")): item for item in report}
        elif isinstance(report, dict):
            # could be {ticker: {...}} or {"portfolio": [...]}
            if "portfolio" in report:
                report_dict = {item.get("ticker", item.get("symbol", "")): item for item in report["portfolio"]}
            else:
                report_dict = report
        else:
            report_dict = {}

        score_errors = []
        rec_errors = []
        for ticker in COMPONENT_SCORES:
            exp_score = expected_score(ticker)
            exp_rec = expected_recommendation(exp_score)
            
            entry = report_dict.get(ticker)
            if entry is None:
                score_errors.append(f"{ticker}: missing from report")
                rec_errors.append(f"{ticker}: missing from report")
                continue
            
            # Find score field
            actual_score = None
            for key in ["score", "composite_score", "total_score", "weighted_score"]:
                if key in entry:
                    actual_score = float(entry[key])
                    break
            
            if actual_score is None:
                score_errors.append(f"{ticker}: no score field found")
            else:
                if abs(actual_score - exp_score) > 0.5:
                    score_errors.append(f"{ticker}: got {actual_score}, expected {exp_score}")
            
            # Find recommendation field
            actual_rec = None
            for key in ["recommendation", "signal", "action", "rating"]:
                if key in entry:
                    actual_rec = str(entry[key]).upper().strip()
                    break
            
            if actual_rec is None:
                rec_errors.append(f"{ticker}: no recommendation field found")
            else:
                if actual_rec != exp_rec:
                    rec_errors.append(f"{ticker}: got '{actual_rec}', expected '{exp_rec}'")

        scores_ok = len(score_errors) == 0
        recs_ok = len(rec_errors) == 0
        
        add_check("weighted_scores_correct", scores_ok,
                  "All weighted scores correct" if scores_ok else f"Score errors: {score_errors}", 3.0)
        add_check("recommendations_correct", recs_ok,
                  "All recommendations correct" if recs_ok else f"Rec errors: {rec_errors}", 2.0)

    except Exception as e:
        add_check("weighted_scores_correct", False, f"Exception reading report: {e}", 3.0)
        add_check("recommendations_correct", False, f"Exception reading report: {e}", 2.0)
else:
    add_check("weighted_scores_correct", False, "No report file to evaluate", 3.0)
    add_check("recommendations_correct", False, "No report file to evaluate", 2.0)

# ── Check 9: TSM has correct non-USD currency stored ─────────────────────────
try:
    out, rc = psql_query("SELECT currency FROM stocks WHERE ticker='TSM';")
    tsm_currency = out.strip()
    passed = "TWD" in tsm_currency
    add_check("non_usd_currency_stored", passed, f"TSM currency='{tsm_currency}', expected 'TWD'", 0.5)
except Exception as e:
    add_check("non_usd_currency_stored", False, f"Exception: {e}", 0.5)

# ── Final score ───────────────────────────────────────────────────────────────
final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}, indent=2))