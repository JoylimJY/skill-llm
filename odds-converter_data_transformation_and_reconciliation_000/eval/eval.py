import sys
import json
import re
from pathlib import Path

def find_report(workspace):
    candidates = list(Path(workspace).rglob("odds_reconciliation_report.txt"))
    return candidates[0] if candidates else None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    checks = []
    report_path = find_report(workspace)

    if not report_path:
        checks.append(check("report_exists", False, "odds_reconciliation_report.txt not found anywhere in workspace"))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append(check("report_exists", True, f"Found at {report_path}"))

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("report_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("report_readable", True, "File is readable"))
    content_lower = content.lower()

    # ---- SECTION 1: BATCH CONVERSION ----
    # Expected American odds: -150, +200, -110, +350, -275
    # Verify section header
    has_batch_section = bool(re.search(r'batch\s+conversion', content, re.IGNORECASE))
    checks.append(check("section1_batch_header", has_batch_section, 
        "Section 'BATCH CONVERSION' found" if has_batch_section else "Missing BATCH CONVERSION section header"))

    # Check all 5 American values appear with correct sign formatting
    batch_american = ["-150", "+200", "-110", "+350", "-275"]
    for val in batch_american:
        found = val in content
        checks.append(check(f"batch_american_{val}", found, 
            f"American odds {val} present in batch table" if found else f"Missing {val} in batch table"))

    # Check Kalshi prices for batch values (must be $X.XX format)
    # -150 -> impl=0.6 -> kalshi=$0.6
    # +200 -> impl=0.3333 -> kalshi=$0.33
    # -110 -> impl=0.5238 -> kalshi=$0.52
    # +350 -> impl=0.2222 -> kalshi=$0.22
    # -275 -> impl=0.7333 -> kalshi=$0.73
    kalshi_expected = ["$0.6", "$0.33", "$0.52", "$0.22", "$0.73"]
    kalshi_found_count = 0
    for kv in kalshi_expected:
        if kv in content:
            kalshi_found_count += 1
    kalshi_check = kalshi_found_count >= 4
    checks.append(check("batch_kalshi_prices", kalshi_check,
        f"Found {kalshi_found_count}/5 expected Kalshi prices in batch section"))

    # Check batch has table format with column headers
    has_table_cols = (
        re.search(r'american', content, re.IGNORECASE) and
        re.search(r'decimal', content, re.IGNORECASE) and
        re.search(r'implied', content, re.IGNORECASE) and
        re.search(r'kalshi', content, re.IGNORECASE) and
        re.search(r'fractional', content, re.IGNORECASE)
    )
    checks.append(check("batch_table_columns", bool(has_table_cols),
        "Batch table has all 5 column headers" if has_table_cols else "Batch table missing some column headers"))

    # ---- SECTION 2: FRACTIONAL CONVERSIONS ----
    # 5/2: dec=3.5, impl=0.2857, amer=+250, kalshi=$0.29
    # 1/4: dec=1.25, impl=0.8, amer=-400, kalshi=$0.8
    # 7/5: dec=2.4, impl=0.4167, amer=+140, kalshi=$0.42
    has_frac_section = bool(re.search(r'fractional\s+conv', content, re.IGNORECASE))
    checks.append(check("section2_fractional_header", has_frac_section,
        "FRACTIONAL CONVERSIONS section found" if has_frac_section else "Missing FRACTIONAL CONVERSIONS section"))

    # Check that fractional inputs appear
    frac_inputs = ["5/2", "1/4", "7/5"]
    for fi in frac_inputs:
        found = fi in content
        checks.append(check(f"frac_input_{fi.replace('/','_')}", found,
            f"Fractional input {fi} present" if found else f"Missing fractional {fi}"))

    # Check American outputs for fractions
    # 5/2 -> +250
    # 1/4 -> -400
    # 7/5 -> +140 (impl=5/12=0.4167, amer = round((1-0.4167)/0.4167 * 100) = round(1.4=140))
    frac_amer_expected = ["+250", "-400", "+140"]
    for fa in frac_amer_expected:
        found = fa in content
        checks.append(check(f"frac_american_{fa}", found,
            f"American output {fa} from fraction found" if found else f"Missing American {fa} for fractional input"))

    # Check Kalshi for fractions: $0.29, $0.8 (or $0.80), $0.42
    frac_kalshi = ["$0.29", "$0.42"]
    for fk in frac_kalshi:
        found = fk in content
        checks.append(check(f"frac_kalshi_{fk}", found,
            f"Kalshi {fk} found for fractional conversion" if found else f"Missing Kalshi {fk}"))
    # 1/4 kalshi: impl=0.8, round(0.8,2)=0.8 -> "$0.8" or "$0.80"
    kalshi_1_4 = "$0.8" in content or "$0.80" in content
    checks.append(check("frac_kalshi_1_4", kalshi_1_4,
        "Kalshi $0.8 found for 1/4" if kalshi_1_4 else "Missing Kalshi $0.8 or $0.80 for 1/4"))

    # ---- SECTION 3: IMPLIED PROBABILITY CONVERSIONS ----
    # championship_game_home: 0.62 -> valid
    # playoff_clincher_away: 65 -> should be treated as 0.65 (percentage interpretation)
    # big_rivalry_draw: 0.45 -> valid
    has_impl_section = bool(re.search(r'implied\s+prob', content, re.IGNORECASE))
    checks.append(check("section3_implied_header", has_impl_section,
        "IMPLIED PROBABILITY CONVERSIONS section found" if has_impl_section else "Missing IMPLIED PROBABILITY section"))

    # 0.62 -> amer=-163 (round(-(0.62/0.38)*100)=round(-163.16)=-163), kalshi=$0.62
    impl_62_amer = re.search(r'-163', content)
    checks.append(check("impl_0.62_american", bool(impl_62_amer),
        "-163 found for 0.62 implied prob" if impl_62_amer else "Missing -163 for 0.62 impl prob"))

    kalshi_62 = "$0.62" in content
    checks.append(check("impl_0.62_kalshi", kalshi_62,
        "$0.62 Kalshi price for 0.62 found" if kalshi_62 else "Missing $0.62 Kalshi for 0.62"))

    # 65 -> must be treated as 0.65 (the proprietary error handling rule)
    # 0.65 -> amer=-186 (round(-(0.65/0.35)*100)=round(-185.71)=-186), kalshi=$0.65
    # The agent must recognize 65 as 65% = 0.65
    impl_65_treated = re.search(r'-18[56]', content)  # -185 or -186
    checks.append(check("impl_65_percent_interpretation", bool(impl_65_treated),
        "65 was correctly interpreted as 0.65 (American -185 or -186 found)" if impl_65_treated 
        else "FAIL: 65 was NOT correctly interpreted as 65% = 0.65, or result missing"))

    kalshi_65 = "$0.65" in content
    checks.append(check("impl_65_kalshi", kalshi_65,
        "$0.65 Kalshi price for 65% found" if kalshi_65 else "Missing $0.65 Kalshi for 65%"))

    # 0.45 -> amer=+122 (round((0.55/0.45)*100)=round(122.22)=+122), kalshi=$0.45
    impl_45_amer = re.search(r'\+122', content)
    checks.append(check("impl_0.45_american", bool(impl_45_amer),
        "+122 found for 0.45 implied prob" if impl_45_amer else "Missing +122 for 0.45 impl prob"))

    kalshi_45 = "$0.45" in content
    checks.append(check("impl_0.45_kalshi", kalshi_45,
        "$0.45 Kalshi for 0.45 found" if kalshi_45 else "Missing $0.45 Kalshi for 0.45"))

    # ---- SECTION 4: DECIMAL CONVERSIONS ----
    # 2.80 -> valid: impl=0.3571, amer=+180, kalshi=$0.36
    # 0.75 -> INVALID (≤1.0), must be flagged/explained
    # 1.65 -> valid: impl=0.6061, amer=-154, kalshi=$0.61
    has_dec_section = bool(re.search(r'decimal\s+conv', content, re.IGNORECASE))
    checks.append(check("section4_decimal_header", has_dec_section,
        "DECIMAL CONVERSIONS section found" if has_dec_section else "Missing DECIMAL CONVERSIONS section"))

    # 2.80 -> amer=+180 (impl=1/2.8=0.3571, (1-0.3571)/0.3571*100=1.8*100=180)
    dec_280_amer = re.search(r'\+18[01]', content)  # +180 or +181
    checks.append(check("decimal_2.80_american", bool(dec_280_amer),
        "+180/+181 found for 2.80 decimal" if dec_280_amer else "Missing +180 for 2.80 decimal"))

    kalshi_280 = re.search(r'\$0\.3[56]', content)
    checks.append(check("decimal_2.80_kalshi", bool(kalshi_280),
        "$0.35 or $0.36 Kalshi for 2.80 found" if kalshi_280 else "Missing Kalshi for 2.80"))

    # 0.75 -> MUST be flagged as invalid (decimal odds must be > 1.0)
    invalid_flagged = bool(re.search(r'0\.75', content) and 
                           re.search(r'invalid|greater than 1|must be.*1|not valid|≤\s*1|<=\s*1|error|cannot', 
                                     content, re.IGNORECASE))
    checks.append(check("decimal_0.75_invalid_flagged", invalid_flagged,
        "0.75 correctly flagged as invalid decimal odds" if invalid_flagged 
        else "FAIL: 0.75 not flagged as invalid (decimal odds must be > 1.0)"))

    # 1.65 -> impl=1/1.65=0.6061, amer=-154, kalshi=$0.61
    dec_165_amer = re.search(r'-15[34]', content)  # -153 or -154
    checks.append(check("decimal_1.65_american", bool(dec_165_amer),
        "-153 or -154 found for 1.65 decimal" if dec_165_amer else "Missing -153/-154 for 1.65 decimal"))

    kalshi_165 = re.search(r'\$0\.6[01]', content)
    checks.append(check("decimal_1.65_kalshi", bool(kalshi_165),
        "$0.60 or $0.61 Kalshi for 1.65 found" if kalshi_165 else "Missing Kalshi for 1.65"))

    # ---- SCORING ----
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4)
    overall_passed = score >= 0.80

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))