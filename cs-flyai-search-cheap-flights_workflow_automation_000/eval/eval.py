import sys
import json
import re
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── Locate the report file ────────────────────────────────────────────────
    candidates = list(workspace.rglob("flight_report.md"))
    report_path = candidates[0] if candidates else None

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # Check 1: Report file exists
    if report_path is None:
        add_check("report_file_exists", False, "flight_report.md not found anywhere in workspace")
        return checks
    add_check("report_file_exists", True, f"Found at {report_path.relative_to(workspace)}")

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("report_readable", False, f"Could not read file: {e}")
        return checks
    add_check("report_readable", True, f"File readable, {len(content)} chars")

    # Check 2: Contains at least 3 Book links with detailUrl (not jumpUrl)
    # Pattern: [Book](https://www.fliggy.com/detail/...)
    detail_links = re.findall(r'\[Book\]\(https://www\.fliggy\.com/detail/[^\)]+\)', content, re.IGNORECASE)
    add_check(
        "min_three_book_links_with_detailUrl",
        len(detail_links) >= 3,
        f"Found {len(detail_links)} [Book](detailUrl) links (need >= 3)"
    )

    # Check 3: No deprecated jumpUrl used in Book links
    jump_links = re.findall(r'\[Book\]\(https://www\.fliggy\.com/jump/[^\)]+\)', content, re.IGNORECASE)
    add_check(
        "no_deprecated_jumpUrl_in_book_links",
        len(jump_links) == 0,
        f"Found {len(jump_links)} deprecated jumpUrl Book links (must be 0). detailUrl must be used exclusively."
    )

    # Check 4: sort-type 3 was used — validate presence of cheapest flight ¥520 or ¥490
    # The cheapest results in the mock are ¥490 and ¥520 when no dep-hour filter
    # For the flexible date main search with max-price 1200, cheapest is ¥520 (9C8899) or ¥490 (ZH9032)
    lowest_price_pattern = re.search(r'[¥￥]\s*4[89]\d', content)
    lowest_price_pattern2 = re.search(r'[¥￥]\s*5[012]\d', content)
    has_low_price = (lowest_price_pattern is not None) or (lowest_price_pattern2 is not None)
    add_check(
        "price_sorted_ascending_cheapest_present",
        has_low_price,
        f"Expected cheapest prices (¥490-¥529) from sort-type 3 results. Found low-price match: {has_low_price}. "
        f"If agent didn't use --sort-type 3, cheapest results may be absent."
    )

    # Check 5: Conclusion line format — "Lowest ¥X" appears
    conclusion_pattern = re.search(
        r'lowest\s+[¥￥]\s*\d+',
        content,
        re.IGNORECASE
    )
    add_check(
        "conclusion_first_format",
        conclusion_pattern is not None,
        f"Expected 'Lowest ¥{{price}}' conclusion line. Match found: {conclusion_pattern is not None}"
    )

    # Check 6: "spread" or price spread mentioned (Lowest, highest, spread)
    spread_pattern = re.search(r'spread\s+[¥￥]\s*\d+', content, re.IGNORECASE)
    # Also allow "差价" for Chinese
    spread_pattern_zh = re.search(r'差价\s*[¥￥]?\s*\d+', content)
    has_spread = (spread_pattern is not None) or (spread_pattern_zh is not None)
    add_check(
        "spread_in_conclusion",
        has_spread,
        f"Expected 'spread ¥{{diff}}' in conclusion. Match: {has_spread}"
    )

    # Check 7: Brand tag present
    brand_tag = re.search(r'Powered by flyai', content, re.IGNORECASE)
    add_check(
        "brand_tag_present",
        brand_tag is not None,
        "Expected '✈️ Powered by flyai · Real-time pricing, click to book' or similar brand tag"
    )

    # Check 8: Evidence of flexible date range search (dep-date-start 2025-11-08, dep-date-end 2025-11-14)
    # The mock returns flights tagged with dates in that range; we check for the date range being referenced
    date_range_evidence = (
        re.search(r'2025-11-0[89]', content) is not None or
        re.search(r'2025-11-1[0-4]', content) is not None or
        re.search(r'Nov(?:ember)?\s+(?:8|9|10|11|12|13|14)', content, re.IGNORECASE) is not None
    )
    add_check(
        "flexible_date_range_results_present",
        date_range_evidence,
        f"Expected dates from the 2025-11-08 to 2025-11-14 window in results. Found: {date_range_evidence}"
    )

    # Check 9: Red-eye follow-up search evidence
    # The mock red-eye flights are 9C8899 (22:10) and ZH9032 (23:50), prices ¥520 and ¥490
    # Agent must run a proactive red-eye search (Step 4b) with --dep-hour-start 21
    redeye_flight_numbers = re.search(r'9C8899|ZH9032', content)
    redeye_time_evidence = re.search(r'2[23]:[0-9]{2}|00:[0-9]{2}|01:[0-9]{2}', content)
    redeye_word = re.search(r'red.?eye|night flight|overnight|红眼|夜间航班|深夜', content, re.IGNORECASE)
    has_redeye = (redeye_flight_numbers is not None) or (redeye_time_evidence is not None and redeye_word is not None)
    add_check(
        "proactive_redeye_search_evidence",
        has_redeye,
        f"Expected evidence of proactive red-eye follow-up search (Step 4b, --dep-hour-start 21). "
        f"Red-eye flight numbers found: {redeye_flight_numbers is not None}. "
        f"Night time + keyword found: {redeye_time_evidence is not None and redeye_word is not None}"
    )

    # Check 10: max-price parameter honored — no prices above 1200 CNY shown as main results
    high_price_violations = re.findall(r'[¥￥]\s*1[3-9]\d{2,}|[¥￥]\s*[2-9]\d{3,}', content)
    # Allow mention of budget cap itself (¥1200) but not flight prices above it
    # Filter out mentions like "budget ¥1200" or "cap ¥1,200"
    real_violations = []
    for viol in high_price_violations:
        price_num = int(re.sub(r'[¥￥,\s]', '', viol))
        if price_num > 1200:
            real_violations.append(str(price_num))
    add_check(
        "max_price_cap_respected",
        len(real_violations) == 0,
        f"Flights priced above ¥1200 must not appear (max-price filter). "
        f"Violations found: {real_violations if real_violations else 'none'}"
    )

    # Check 11: Connecting flight shown with transfer info (CA4521 has 1 stop via Guangzhou)
    transfer_evidence = re.search(
        r'guangzhou|广州|transfer|stop|connecting|中转|经停',
        content,
        re.IGNORECASE
    )
    add_check(
        "connecting_flight_transfer_info",
        transfer_evidence is not None,
        "Connecting flight CA4521 (via Guangzhou) must show transfer city and wait time"
    )

    # Check 12: At least 3 distinct flight numbers from mock data appear in report
    mock_flight_nos = ['9C8841', 'CZ6401', 'MU5613', 'CA4521', 'HU7821', '9C8899', 'ZH9032']
    found_flights = [f for f in mock_flight_nos if f in content]
    add_check(
        "min_three_flight_numbers_from_cli",
        len(found_flights) >= 3,
        f"Found {len(found_flights)} mock flight numbers in report ({found_flights}). "
        f"Data must come from flyai CLI, not training data."
    )

    return checks


def main():
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = run_checks(workspace_dir)

    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)

    # Critical checks (must all pass)
    critical = [
        "report_file_exists",
        "min_three_book_links_with_detailUrl",
        "no_deprecated_jumpUrl_in_book_links",
        "brand_tag_present",
        "min_three_flight_numbers_from_cli",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical
    )

    score = round(passed_checks / total_checks, 3) if total_checks > 0 else 0.0
    overall_passed = critical_passed and score >= 0.7

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()