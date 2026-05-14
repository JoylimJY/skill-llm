import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ─── MARCH 2026 EXPENSE FILE ───────────────────────────────────────────────
    march_file = workspace / "expenses" / "2026-03.md"
    try:
        assert march_file.exists(), "File does not exist"
        march_content = march_file.read_text(encoding="utf-8")
        add_check("march_file_exists", True, f"Found {march_file}")
    except Exception as e:
        add_check("march_file_exists", False, str(e))
        march_content = ""

    # ─── APRIL 2026 EXPENSE FILE ───────────────────────────────────────────────
    april_file = workspace / "expenses" / "2026-04.md"
    try:
        assert april_file.exists(), "File does not exist"
        april_content = april_file.read_text(encoding="utf-8")
        add_check("april_file_exists", True, f"Found {april_file}")
    except Exception as e:
        add_check("april_file_exists", False, str(e))
        april_content = ""

    # ─── MARCH ENTRY COUNT ────────────────────────────────────────────────────
    try:
        # Count data rows (lines with | that are not header or separator)
        march_rows = [
            l.strip() for l in march_content.splitlines()
            if l.strip().startswith("|")
            and not l.strip().startswith("|---")
            and not l.strip().startswith("| Date")
        ]
        # Expected 10 transactions in March
        expected_march = 10
        passed = len(march_rows) >= expected_march
        add_check(
            "march_transaction_count",
            passed,
            f"Found {len(march_rows)} rows, expected at least {expected_march}"
        )
    except Exception as e:
        add_check("march_transaction_count", False, str(e))

    # ─── APRIL ENTRY COUNT ────────────────────────────────────────────────────
    try:
        april_rows = [
            l.strip() for l in april_content.splitlines()
            if l.strip().startswith("|")
            and not l.strip().startswith("|---")
            and not l.strip().startswith("| Date")
        ]
        expected_april = 8
        passed = len(april_rows) >= expected_april
        add_check(
            "april_transaction_count",
            passed,
            f"Found {len(april_rows)} rows, expected at least {expected_april}"
        )
    except Exception as e:
        add_check("april_transaction_count", False, str(e))

    # ─── MARCH KEY ENTRIES: VND AMOUNTS FORMATTED WITH COMMAS ─────────────────
    try:
        # Check specific amounts appear in march file (comma-formatted)
        expected_amounts_march = ["55,000", "85,000", "450,000", "260,000", "59,000", "780,000", "4,500,000", "320,000"]
        missing = [a for a in expected_amounts_march if a not in march_content]
        passed = len(missing) == 0
        add_check(
            "march_amounts_comma_formatted",
            passed,
            f"Missing amounts: {missing}" if missing else "All expected amounts found with comma formatting"
        )
    except Exception as e:
        add_check("march_amounts_comma_formatted", False, str(e))

    # ─── APRIL KEY ENTRIES: VND AMOUNTS FORMATTED WITH COMMAS ────────────────
    try:
        expected_amounts_april = ["75,000", "350,000", "340,000", "600,000", "180,000", "1,200,000", "450,000"]
        missing = [a for a in expected_amounts_april if a not in april_content]
        passed = len(missing) == 0
        add_check(
            "april_amounts_comma_formatted",
            passed,
            f"Missing amounts: {missing}" if missing else "All expected amounts found with comma formatting"
        )
    except Exception as e:
        add_check("april_amounts_comma_formatted", False, str(e))

    # ─── CATEGORIES ARE PROPERLY ASSIGNED ─────────────────────────────────────
    try:
        # March: Housing (rent), Utilities (electricity), Personal Care (haircut), Subscriptions, Public Transport
        required_categories_march = ["Housing", "Utilities", "Subscriptions", "Public Transport", "Personal Care"]
        missing_cats = [c for c in required_categories_march if c not in march_content]
        passed = len(missing_cats) == 0
        add_check(
            "march_categories_correct",
            passed,
            f"Missing categories in March: {missing_cats}" if missing_cats else "All required categories present"
        )
    except Exception as e:
        add_check("march_categories_correct", False, str(e))

    try:
        # April: Education, Parking, Fitness, Healthcare, Clothing/Dining
        required_categories_april = ["Education", "Parking", "Fitness", "Healthcare"]
        missing_cats = [c for c in required_categories_april if c not in april_content]
        passed = len(missing_cats) == 0
        add_check(
            "april_categories_correct",
            passed,
            f"Missing categories in April: {missing_cats}" if missing_cats else "All required categories present"
        )
    except Exception as e:
        add_check("april_categories_correct", False, str(e))

    # ─── TAGS PRESENT ─────────────────────────────────────────────────────────
    try:
        # Tags in march: work,morning or work should appear; commute for transport
        march_has_tags = any(tag in march_content for tag in ["work", "morning", "commute", "social"])
        add_check(
            "march_tags_present",
            march_has_tags,
            "Tags found in March file" if march_has_tags else "No expected tags found in March file"
        )
    except Exception as e:
        add_check("march_tags_present", False, str(e))

    try:
        april_has_tags = any(tag in april_content for tag in ["learning", "health", "fitness", "weekend", "social"])
        add_check(
            "april_tags_present",
            april_has_tags,
            "Tags found in April file" if april_has_tags else "No expected tags found in April file"
        )
    except Exception as e:
        add_check("april_tags_present", False, str(e))

    # ─── DATES ARE CORRECTLY BACKDATED ────────────────────────────────────────
    try:
        march_dates = ["2026-03-03", "2026-03-10", "2026-03-17", "2026-03-24"]
        missing_dates = [d for d in march_dates if d not in march_content]
        passed = len(missing_dates) == 0
        add_check(
            "march_dates_backdated",
            passed,
            f"Missing dates: {missing_dates}" if missing_dates else "All March dates correctly backdated"
        )
    except Exception as e:
        add_check("march_dates_backdated", False, str(e))

    try:
        april_dates = ["2026-04-02", "2026-04-09", "2026-04-15", "2026-04-22"]
        missing_dates = [d for d in april_dates if d not in april_content]
        passed = len(missing_dates) == 0
        add_check(
            "april_dates_backdated",
            passed,
            f"Missing dates: {missing_dates}" if missing_dates else "All April dates correctly backdated"
        )
    except Exception as e:
        add_check("april_dates_backdated", False, str(e))

    # ─── COMPARISON REPORT FILE ───────────────────────────────────────────────
    report_candidates = list(workspace.rglob("spending_comparison.json"))
    if report_candidates:
        report_file = report_candidates[0]
        add_check("comparison_report_exists", True, f"Found at {report_file}")
    else:
        add_check("comparison_report_exists", False, "spending_comparison.json not found anywhere in workspace")
        report_file = None

    # ─── REPORT JSON STRUCTURE ────────────────────────────────────────────────
    report_data = None
    if report_file:
        try:
            report_data = json.loads(report_file.read_text(encoding="utf-8"))
            add_check("comparison_report_valid_json", True, "JSON parses correctly")
        except Exception as e:
            add_check("comparison_report_valid_json", False, f"JSON parse error: {e}")

    if report_data is not None:
        # Must contain both months
        try:
            has_march = any(
                "2026-03" in str(v) or (isinstance(v, dict) and "2026-03" in str(v))
                for v in [report_data, str(report_data)]
            )
            # More robust: check if "2026-03" appears anywhere in the JSON string
            report_str = json.dumps(report_data)
            has_march = "2026-03" in report_str
            has_april = "2026-04" in report_str
            add_check(
                "report_contains_both_months",
                has_march and has_april,
                f"March present: {has_march}, April present: {has_april}"
            )
        except Exception as e:
            add_check("report_contains_both_months", False, str(e))

        # Must contain totals (numeric values that are large — VND scale)
        try:
            # March total should be: 55000+85000+450000+260000+59000+200000+780000+65000+4500000+320000+120000 = 6,894,000
            # April total should be: 75000+350000+340000+15000+600000+180000+1200000+450000 = 3,210,000
            report_str = json.dumps(report_data)
            # Look for large numbers (at least 6 digits) suggesting proper VND totals
            large_numbers = re.findall(r'\b(\d{6,})\b', report_str)
            has_large_numbers = len(large_numbers) >= 2
            add_check(
                "report_contains_totals",
                has_large_numbers,
                f"Found large numeric totals: {large_numbers[:5]}" if large_numbers else "No VND-scale totals found"
            )
        except Exception as e:
            add_check("report_contains_totals", False, str(e))

        # Must have category breakdown
        try:
            report_str = json.dumps(report_data)
            # These categories should appear in the breakdown
            required_cats = ["Housing", "Coffee", "Dining", "Subscriptions"]
            found_cats = [c for c in required_cats if c in report_str]
            passed = len(found_cats) >= 3
            add_check(
                "report_has_category_breakdown",
                passed,
                f"Found categories in report: {found_cats}"
            )
        except Exception as e:
            add_check("report_has_category_breakdown", False, str(e))

    # ─── MARKDOWN TABLE FORMAT (not raw HTML or CSV) ──────────────────────────
    try:
        has_pipe_table_march = "|" in march_content and "|---|" in march_content.replace(" ", "").replace("-", "-")
        has_separator = bool(re.search(r'\|[-\s|]+\|', march_content))
        add_check(
            "march_uses_markdown_table",
            has_pipe_table_march and has_separator,
            "March file uses proper markdown pipe table format"
        )
    except Exception as e:
        add_check("march_uses_markdown_table", False, str(e))

    # ─── FINAL SCORE ──────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall_passed = score >= 0.80

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))